library(RPostgreSQL)
driver <- PostgreSQL()
host <- Sys.getenv('HOST', 'localhost')
dbname <- Sys.getenv('DATABASE_NAME', 'econometrika')
dbuser <- Sys.getenv('DATABASE_USER')
dbpass <- Sys.getenv('DATABASE_PASSWORD')
con <- dbConnect(driver, host=host, dbname=dbname, user=dbuser, password=dbpass)

stmt <- dbSendQuery(con, "select * from analysis_split order by date desc")
splits <- fetch(stmt, -1)
dbClearResult(stmt)

args <- commandArgs()
all_deleted <- FALSE
min_date <- Sys.Date() - 4

if (length(args) > 1) {
    stmt <- dbSendQuery(con, "select sy.*, q.last_date from analysis_symbol sy join (select symbol_id, max(date) as last_date from analysis_symbolquote group by symbol_id) q on symbol_id = sy.id where ticker = $1", args[2])
    min_date <- ifelse(!is.na(args[3]), as.Date(args[3]), min_date)
    class(min_date) <- 'Date'
} else {
    stmt <- postgresqlExecStatement(con, 'delete from analysis_periodreturn')
    dbClearResult(stmt)
    all_deleted <- TRUE
    stmt <- dbSendQuery(con, "select sy.*, q.last_date from analysis_symbol sy join (select symbol_id, max(date) as last_date from analysis_symbolquote group by symbol_id) q on symbol_id = sy.id ")
}
symbols <- fetch(stmt, -1)
dbClearResult(stmt)

for (rs in rownames(symbols)) {
    symbol <- symbols[rs,]
    if (!all_deleted) {
        stmt <- postgresqlExecStatement(con, 'delete from analysis_periodreturn where symbol_id = $1', symbol$id)
        dbClearResult(stmt)
    }
    if (min_date > symbol$last_date) next
    periods <- c('1D', '1W', '1M', '3M', '6M', 'YTD', '1Y')
    stmt <- dbSendQuery(con, "
        select * from (select sq.* from analysis_symbolquote sq where sq.symbol_id  = $1 order by date desc limit 2) s1
        union
        select * from (select sq.* from analysis_symbolquote sq where sq.symbol_id  = $1 and date <= $2::date - interval '7 days' and date >= $2 - interval '10 days' order by date desc limit 1) s2
        union
        select * from (select sq.* from analysis_symbolquote sq where sq.symbol_id  = $1 and date <= $2::date - interval '1 month' and date >= $2 - interval '2 months' order by date desc limit 1) s3
        union
        select * from (select sq.* from analysis_symbolquote sq where sq.symbol_id  = $1 and date <= $2::date - interval '3 months' and date >= $2 - interval '5 months' order by date desc limit 1) s4
        union
        select * from (select sq.* from analysis_symbolquote sq where sq.symbol_id  = $1 and date <= $2::date - interval '6 months' and date >= $2 - interval '8 months' order by date desc  limit 1) s5
        union
        select * from (select sq.* from analysis_symbolquote sq where sq.symbol_id  = $1 and date <= date_trunc('year', $2) and date >= $2 - interval '1.5 year'  order by date asc limit 1) s6
        union
        select * from (select sq.* from analysis_symbolquote sq where sq.symbol_id  = $1 and date <= $2::date - interval '1 year' and date >= $2 - interval '1.5 year' order by date desc limit 1) s7
        order by date asc
    ", c(symbol$id, as.character(symbol$last_date)))
    quotes <- fetch(stmt, -1)
    dbClearResult(stmt)
    if (nrow(quotes) == 0) next
    print(paste0('Generating for ', symbol$name))
    stmt <- dbSendQuery(con, "select d.* from analysis_dividend d where d.symbol_id = $1 and ex_date >= $2::date - interval '1.5 year' order by ex_date desc", c(symbol$id, as.character(min_date)))
    dividends <- fetch(stmt, -1)
    dbClearResult(stmt)
    symbol_splits = splits[splits$symbol == symbol$id,]
    for (r in rownames(symbol_splits)) {
        split <- symbol_splits[r,]
        dividends[dividends$ex_date < split$date,]$gross <- dividends[dividends$ex_date < split$date,]$gross * split$proportion
    }
    for (r in rownames(dividends)) {
        dividend <- dividends[r,]
        ex_date <- dividend$ex_date
        ex_date_index <- NA
        j <- 0
        if (ex_date > tail(quotes, 1)$date) next
        while (is.na(ex_date_index)) {
            ex_date_index <- match(ex_date + j, quotes$date)
            j <- j + 1
        }
        m <- quotes$close[ex_date_index] / (quotes$close[ex_date_index] + dividend$gross)
        quotes$close <- c(round(quotes$close[quotes$date < ex_date] * m, 3), quotes$close[quotes$date >= ex_date])
    }
    period_returns <- round(c(
        ifelse(nrow(quotes) > 1, tail(quotes, 1)$close / head(tail(quotes, 2), 1)$close - 1, NA),
        ifelse(nrow(quotes) > 2, tail(quotes, 1)$close / head(tail(quotes, 3), 1)$close - 1, NA),
        ifelse(nrow(quotes) > 3, tail(quotes, 1)$close / head(tail(quotes, 4), 1)$close - 1, NA),
        ifelse(nrow(quotes) > 4, tail(quotes, 1)$close / head(tail(quotes, 5), 1)$close - 1, NA),
        ifelse(nrow(quotes) > 5, tail(quotes, 1)$close / head(tail(quotes, 6), 1)$close - 1, NA),
        ifelse(nrow(quotes) > 6, tail(quotes, 1)$close / head(tail(quotes, 7), 1)$close - 1, NA),
        ifelse(nrow(quotes) > 7, tail(quotes, 1)$close / head(tail(quotes, 8), 1)$close - 1, NA)), 4)
    params <- rbind(symbol$id, periods, period_returns)
    params <- params[,!is.na(period_returns)]
    if (!ncol(params) > 0) next
    placeholders <- paste(apply(array(paste0('$', 1:length(params)), dim=c(3,ncol(params))), 2, function(r) paste('(', paste(r, collapse=','), ')')), collapse=',')
    stmt <- postgresqlExecStatement(con, paste('insert into analysis_periodreturn (symbol_id, period_type, period_return) values ',
        placeholders), c(params)) 
    dbClearResult(stmt)
}
dbDisconnect(con)
