library(RPostgreSQL)
library(quantmod)

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

hollydays <- as.Date(c(
   '2017-04-14', '2017-04-17', '2017-05-01', '2017-12-25', '2017-12-26',
   '2016-01-01', '2016-03-25', '2016-03-28', '2016-12-26',
   '2015-01-01', '2015-04-03', '2015-04-06', '2015-05-01', '2015-12-25', 
   '2014-01-01', '2014-04-18', '2014-04-21', '2014-05-01', '2014-12-25', '2014-12-26', 
   '2013-01-01', '2013-03-29', '2013-04-01', '2013-05-01', '2013-12-25', '2013-12-26', 
   '2012-04-06', '2012-04-09', '2012-05-01', '2012-12-25', '2012-12-26',
   '2011-04-22', '2011-04-25', '2011-12-26',
   '2010-01-01', '2010-04-02', '2010-04-05', '2010-12-24', '2010-12-31',
   '2009-01-01', '2009-04-10', '2009-04-13', '2009-05-01', '2009-12-24', '2009-12-25', '2009-12-31', 
   '2008-01-01', '2008-04-21', '2008-04-24', '2008-05-01', '2008-12-24', '2008-12-25', '2008-12-26', '2008-12-31',
   '2007-01-01', '2007-04-06', '2007-04-09', '2007-05-01', '2007-12-24', '2007-12-25', '2007-12-26', '2007-12-31',
   '2006-01-06', '2006-04-14', '2006-04-17', '2006-05-01', '2006-12-25', '2006-12-26', 
   '2005-01-06', '2005-03-25', '2005-03-28', '2005-12-26', 
   '2004-01-01', '2004-01-06', '2004-04-09', '2004-04-12', '2004-08-16', '2004-10-12', 
       '2004-11-01', '2004-12-06', '2004-12-08',  '2004-12-24', '2004-12-31',
   '2003-01-01', '2003-01-06', '2003-04-18', '2003-04-21', '2003-05-01', '2003-08-15',
       '2003-12-08',  '2003-12-24',  '2003-12-25',  '2003-12-26', '2003-12-31',
   '2002-01-01', '2002-03-29', '2002-04-01', '2002-05-01', '2002-08-15', '2002-11-01',
       '2002-12-06',  '2002-12-24',  '2002-12-25',  '2002-12-26', '2002-12-31',
   '2001-01-01', '2001-04-13', '2001-04-16', '2001-05-01', '2001-08-15', '2001-10-12',
       '2001-12-06',  '2001-12-24',  '2001-12-25',  '2001-12-26', '2001-12-31',
   '2000-12-26', '2000-12-25', '2000-12-08', '2000-12-06', '2000-11-01', '2000-10-12', '2000-05-01',
       '2000-04-24', '2000-04-21', '2000-01-06',
   '1999-12-31', '1999-12-24', '1999-12-08', '1999-12-06', '1999-11-01', '1999-10-12', '1999-04-05',
       '1999-04-02', '1999-04-01', '1999-01-06', '1999-01-01',
   '1998-12-31', '1998-12-25', '1998-12-24', '1998-12-08', '1998-10-12',
       '1998-06-01', '1998-04-13', '1998-04-10', '1998-04-09', '1998-01-06', '1998-01-01',
   '1997-12-25', '1997-12-24', '1997-12-08', '1997-08-15', '1997-05-01', '1997-03-28', '1997-03-27', '1997-01-06', '1997-01-01',
   '1996-12-25', '1996-12-24', '1996-12-06', '1996-11-01', '1996-08-15', '1996-05-01', '1996-04-05', '1996-04-04', '1996-01-01',
   '1995-12-25', '1995-12-08', '1995-12-06', '1995-11-01', '1995-10-12', '1995-08-15',
       '1995-05-01', '1995-04-14', '1995-04-13', '1995-01-06',
   '1994-12-26', '1994-12-08', '1994-12-06', '1994-11-01', '1994-10-12', '1994-08-15',
       '1994-04-01', '1994-03-31', '1994-01-06'))

symbols <- fetch(stmt, -1)
dbClearResult(stmt)

for (rs in rownames(symbols)) {
    symbol <- symbols[rs,]
    print(paste0('Filling for ', symbol$name))
    stmt <- dbSendQuery(con, "select sq.* from analysis_symbolquote sq where sq.symbol_id  = $1 order by date", symbol$id)
    quotes_db <- fetch(stmt, -1)
    dbClearResult(stmt)
    if (!nrow(quotes_db) > 0) next
    days <- seq.Date(head(quotes_db, 1)$date, tail(quotes_db, 1)$date, 1)
    days <- days[!days %in% hollydays & !weekdays(days) %in% c('sábado', 'domingo')]
    missing <- setdiff(days, quotes_db$date)
    class(missing) <- 'Date'
    missing <- tapply(missing, substring(missing, 1, 4), c)
    for (m in missing) {
        ret <- try (quotes_yh <- getSymbols(symbol$key, from=min(m), to=max(m), auto.assign=F))
        if (inherits(ret, 'try-error')) {
            message(ret)
            next
        }
        for (m2 in m) 
            class(m2) <- 'Date'
            if (!as.Date(m2) %in% index(quotes_yh)) next
            stmt <- postgresqlExecStatement(con, 'insert into analysis_symbolquote (symbol_id, date, open, high, low, close, volume)
                values($1, $2, $3, $4, $5, $6, $7)',
                c(symbol$id, as.character(m2), quotes_yh[m2,1], quotes_yh[m2,2], quotes_yh[m2,3], quotes_yh[m2,4], quotes_yh[m2,5]))
            dbClearResult(stmt)
    }
}
dbDisconnect(con)
