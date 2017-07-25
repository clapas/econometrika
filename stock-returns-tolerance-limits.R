library(RPostgreSQL)
driver <- PostgreSQL()
con <- dbConnect(driver, host='localhost', dbname='econometrika', user='econometrika', password='^}jy5nnr(fVXK/Fw')
stmt <- dbSendQuery(con, "select sq.* from analysis_stockquote sq join analysis_symbol sy on (sq.symbol_id = sy.id) where ticker = 'ibex35' order by date")
ibex35 <- fetch(stmt, -1)
dbClearResult(stmt)
ibex35$rate <- c(0, log(tail(ibex35$close, -1)/head(ibex35$close, -1)))

options("scipen"=-2, "digits"=4)
libex35 <- length(ibex35$rate)
category <- 'analysis.stock-returns-tolerance-limits'
stmt <- postgresqlExecStatement(con, 'delete from analysis_keyvalue where category = $1', c(category))
dbClearResult(stmt)
stmt <- postgresqlExecStatement(con, 'insert into analysis_keyvalue (category, key, value) values ($1, $2, $3), ($4, $5, $6)',
    c(category, 'last_ibex35_date', as.character(tail(ibex35$date, 1)), category, 'ibex35_n_observations', libex35))
dbClearResult(stmt)
stmt <- postgresqlExecStatement(con, 'insert into analysis_keyvalue (category, key, value) values ($1, $2, $3), ($4, $5, $6)',
    c(category, 'ibex35_max_drop_date', as.character(ibex35$date[match(min(ibex35$rate), ibex35$rate)]), category, 'ibex35_max_drop', prettyNum(exp(min(ibex35$rate))*100 - 100)))
dbClearResult(stmt)
stmt <- postgresqlExecStatement(con, 'insert into analysis_keyvalue (category, key, value) values ($1, $2, $3), ($4, $5, $6)',
    c(category, 'ibex35_max_gain_date', as.character(ibex35$date[match(max(ibex35$rate), ibex35$rate)]), category, 'ibex35_max_gain', prettyNum(exp(max(ibex35$rate))*100 - 100)))
dbClearResult(stmt)
library(tolerance)
stmt <- postgresqlExecStatement(con, 'insert into analysis_keyvalue (category, key, value) values ($1, $2, $3), ($4, $5, $6)',
    c(category, 'ibex35_0.999_bitol_D', prettyNum(distfree.est(libex35, 0.001, side=2)), category, 'ibex35_0.99_bitol_D', prettyNum(distfree.est(libex35, 0.01, side=2))))
dbClearResult(stmt)
stmt <- postgresqlExecStatement(con, 'insert into analysis_keyvalue (category, key, value) values ($1, $2, $3), ($4, $5, $6)',
    c(category, 'ibex35_0.999_unitol_D', prettyNum(distfree.est(libex35, 0.001, side=1)), category, 'ibex35_0.99_unitol_D', prettyNum(distfree.est(libex35, 0.01, side=1))))
dbClearResult(stmt)
dbDisconnect(con)
