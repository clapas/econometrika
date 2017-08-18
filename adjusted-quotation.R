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

stmt <- dbSendQuery(con, "select * from analysis_symbol")
symbols <- fetch(stmt, -1)
#symbols <- data.frame(id=114, ticker='REP', name='REPSOL', market='MC')
dbClearResult(stmt)

library(plotly)
library(htmltools)
library(knitr)
library(TTR)
library(xts)
libpath <- file.path(getwd(), './media/plotly_lib')
bpath <- './media/'
for (rs in rownames(symbols)) {
    symbol <- symbols[rs,]
    stmt <- dbSendQuery(con, "select sq.* from analysis_symbolquote sq where sq.symbol_id  = $1 order by date", symbol$id)
    quotes <- fetch(stmt, -1)
    dbClearResult(stmt)
    if (nrow(quotes) == 0) next
    print(paste0('Generating for ', symbol$name))
    stmt <- dbSendQuery(con, "select d.* from analysis_dividend d where d.symbol_id = $1 order by ex_date desc", symbol$id)
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
        quotes$low <- c(round(quotes$low[quotes$date < ex_date] * m, 3), quotes$low[quotes$date >= ex_date])
        quotes$high <- c(round(quotes$high[quotes$date < ex_date] * m, 3), quotes$high[quotes$date >= ex_date])
    }
    date <- quotes$date
    quotes <- xts(quotes[, c('open', 'high', 'low', 'close', 'volume')], quotes$date)
    colnames(quotes) <- c('Open', 'High', 'Low', 'Close', 'Volume')
    if (length(quotes$Close) > 50) {
        bbands <- BBands(quotes[, c('High', 'Low', 'Close')], 50, sd=2.1)
        quotes <- cbind(quotes, bbands)
        dyg1 <- dygraph(quotes[, c('Close', 'up', 'dn', 'mavg')], width='100%', height='400px', group='symbol', ylab='Cotización (€)') %>%
            dySeries(c('dn', 'Close', 'up'), strokeWidth=1, label='Cierre') %>%
            dySeries(c('mavg'), strokeWidth=0.5, label='Media móvil')
    }
    else dyg1 <- dygraph(quotes[, c('Close')], width='100%', height='400px', group='symbol', ylab='Cotización (€)') %>%
        dySeries(c('Close'), strokeWidth=1, label='Cierre')
    dyg1 <- dyg1 %>% dyOptions(colors = RColorBrewer::brewer.pal(3, 'Set2'), mobileDisableYTouch=TRUE)
    dyg2 <- dygraph(quotes[,'Volume'], width='100%', height='150px', group='symbol', ylab='Nº acciones') %>%
        dySeries('Volume', label='Volumen') %>%
        dyRangeSelector() %>%
        dyOptions(fillGraph=TRUE, fillAlpha=0.7, colors=RColorBrewer::brewer.pal(4, 'Set2')[3:4], mobileDisableYTouch=TRUE)
    slug <- paste0(tolower(symbol$ticker), '-adjusted-quote')
    wpath <- file.path(getwd(), bpath, paste0(slug, '.html'))
    knit(text='<!--begin.rcode echo=F
        tagList(dyg1)
        tagList(dyg2)
    end.rcode-->', output=wpath)
    stmt <- postgresqlExecStatement(con, 'delete from analysis_plot where slug = $1', slug)
    dbClearResult(stmt)
    stmt <- postgresqlExecStatement(con, 'insert into analysis_plot (file_path, slug, title, lang_code_id, symbol_id, type, html_above) values ($1, $2, $3, $4, $5, $6, $7)',
        c(wpath, slug, paste0(symbol$name, ': cotización ajustada'), 'es', symbol$id, 'quote', ''))
    dbClearResult(stmt)
    print(paste0('Done with ', symbol$name))
}
dbDisconnect(con)
