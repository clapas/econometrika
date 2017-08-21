library(RPostgreSQL)
library(quantmod)

OVERLAPPING = 4

driver <- PostgreSQL()
host <- Sys.getenv('HOST', 'localhost')
dbname <- Sys.getenv('DATABASE_NAME', 'econometrika')
dbuser <- Sys.getenv('DATABASE_USER')
dbpass <- Sys.getenv('DATABASE_PASSWORD')
con <- dbConnect(driver, host=host, dbname=dbname, user=dbuser, password=dbpass)

args <- commandArgs()
sql <- "
    select sy.*, ss.key
        from analysis_symbol sy 
            join analysis_symbolsource ss on ss.symbol_id = sy.id 
        where ss.name = 'quantmod' and ss.type = 'quote'"

if (!is.na(args[1])) {
    sql <- paste(sql, "and ticker = $1")
    stmt <- dbSendQuery(con, sql, args[1])
} else stmt <- dbSendQuery(con, sql)

symbols <- fetch(stmt, -1)
dbClearResult(stmt)

if (!is.na(args[2])) {
    min_ex_date <- as.Date(args[2])
} else min_ex_date <- as.Date('1839-07-08')

for (rs in rownames(symbols)) {
    symbol <- symbols[rs,]
    print(paste0('Fetching for ', symbol$name))
    ret <- try (all_dividends <- getDividends(symbol$key))
    if (inherits(ret, 'error')) {
        message(ret)
        next
    }
    stmt <- dbSendQuery(con, "select d.* from analysis_dividend d where d.symbol_id = $1 order by ex_date desc", symbol$id)
    existing_dividends <- fetch(stmt, -1)
    dbClearResult(stmt)
    for (i in index(all_dividends)) {
        i_date <- as.Date(i)
        if (i_date < min_ex_date) next
        for (d in rownames(existing_dividends)) {
            div <- existing_dividends[d,]
            isnew <- T
            if (abs(i_date -  div$ex_date) <= OVERLAPPING) {
                isnew <- F
                break
            }
        }
        if (isnew) {
            gross <- all_dividends[i_date]
            stmt <- postgresqlExecStatement(con, 'insert into analysis_dividend (symbol_id, ex_date, gross, type) values ($1, $2, $3, \'\')',
                c(symbol$id, as.character(i_date), gross)) 
            dbClearResult(stmt)
        }
    }
}
dbDisconnect(con)
