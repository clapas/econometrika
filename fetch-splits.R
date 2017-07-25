library(RPostgreSQL)
driver <- PostgreSQL()
con <- dbConnect(driver, host='localhost', dbname='econometrika', user='econometrika', password='^}jy5nnr(fVXK/Fw')

stmt <- dbSendQuery(con, "select * from analysis_symbol")
symbols <- fetch(stmt, -1)
dbClearResult(stmt)

for (rs in rownames(symbols)) {
    symbol <- symbols[rs, ]
    tryCatch({
        last_split <- as.Date('0000-01-01') # anno zero
        if (!is.na(symbol$quantmod_lastsplit_date)) last_split <- symbol$quantmod_lastsplit_date
        new_splits <- getSplits(symbol$quantmod_ticker, from=last_split + 1)
        if (!is.na(new_splits) && length(new_splits) > 0) for (i in 1:nrow(new_splits)) {
            stmt <- postgresqlExecStatement(con, 'update analysis_stockquote set open = open * $1, high = high * $2, low = low * $3, close = close * $4 where symbol_id = $5 and date <= $6', c(rep(new_splits[[i]], 4), symbol$id, as.character(index(new_splits[i]))))
            dbClearResult(stmt)
            stmt <- postgresqlExecStatement(con, 'update analysis_symbol set quantmod_lastsplit_date = $1, quantmod_lastsplit_ratio = $2 where id = $3', c(as.character(index(new_splits[i])), new_splits[[i]], symbol$id))
            dbClearResult(stmt)
        }
    }, error = function(cond) {
        print(cond$message)
        if (cond$message == 'HTTP error 400.') return(NA)
        else {
            dbDisconnect(con)
            stop(cond)
        }
    })
}
dbDisconnect(con)
print('DONE!')
