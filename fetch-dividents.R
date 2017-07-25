library(RPostgreSQL)
driver <- PostgreSQL()
con <- dbConnect(driver, host='localhost', dbname='econometrika', user='econometrika', password='^}jy5nnr(fVXK/Fw')

stmt <- dbSendQuery(con, "select sy.id, quantmod_ticker, max(ex_date) ex_date from analysis_dividend d right join analysis_symbol sy on (d.symbol_id = sy.id) group by sy.id;")
last_dividends <- fetch(stmt, -1)
dbClearResult(stmt)

library(quantmod)
for (rs in rownames(last_dividends)) {
    last_dividend <- last_dividends[rs,]
    tryCatch({
        new_dividends <- getDividends(last_dividend$quantmod_ticker, from=last_dividend$ex_date + 1)
        if (length(new_dividends) > 0) for (i in 1:nrow(new_dividends)) {
            stmt <- postgresqlExecStatement(con, 'insert into analysis_dividend (ex_date, gross, type, symbol_id) values ($1, $2, $3, $4)',
                c(as.character(index(new_dividends[i])), new_dividends[[i]], '', last_dividend$id))
            dbClearResult(stmt)
        }
    }, error = function(cond) {
        if (cond$message == 'HTTP error 400.') return(NA)
        else {
            dbDisconnect(con)
            stop(cond)
        }
    })
}
dbDisconnect(con)
print('DONE!')
