library(RPostgreSQL)
driver <- PostgreSQL()
con <- dbConnect(driver, host='localhost', dbname='econometrika', user='econometrika', password='^}jy5nnr(fVXK/Fw')

stmt <- dbSendQuery(con, "
    select sy.id, sp.*, ss.key, sy.ticker
        from analysis_symbol sy
            left join (
                select symbol_id, max(date) as date
                    from analysis_split
                        group by symbol_id) sp on (sy.id = sp.symbol_id)
            join analysis_symbolsource ss on ss.symbol_id = sy.id
        where ss.name = 'quantmod'") # and ss.type = 'split'") # omit type, quantmod source is suitable for all types

symbols <- fetch(stmt, -1)
dbClearResult(stmt)

library(quantmod)
library(dplyr)
f <- F
for (rs in rownames(symbols)) {
    symbol <- symbols[rs, ]
    if (symbol$ticker == 'PAC') f <- T
    if (!f) next
    tryCatch({
        from_split <- ifelse(!is.na(symbol$date), as.character(symbol$date + 1), as.Date('0000-01-01')) # else anno zero
        new_splits <- getSplits(symbol$key, from=from_split)
        if (!is.na(new_splits) && length(new_splits) > 0) for (i in 1:nrow(new_splits)) {
            print(paste('New split for', symbol$ticker, new_splits[i]))
            stmt <- postgresqlExecStatement(con, 'update analysis_symbolquote set open = open * $1, high = high * $2, low = low * $3, close = close * $4 where symbol_id = $5 and date <= $6', c(rep(new_splits[[i]], 4), symbol$id, as.character(index(new_splits[i]))))
            dbClearResult(stmt)
            stmt <- postgresqlExecStatement(con, 'insert into analysis_split(date, proportion, symbol_id) values ($1, $2, $3)', c(as.character(index(new_splits[i])), new_splits[[i]], symbol$id))
            dbClearResult(stmt)
        } else print(paste('No new splits for', symbol$ticker))
    }, error = function(cond) {
        print(cond$message)
        print(paste('Skip', symbol$ticker))
        if (!cond$message %in% c('HTTP error 400.', 'HTTP error 404.')) {
            dbDisconnect(con)
            stop(cond)
        }
    })
}
dbDisconnect(con)
