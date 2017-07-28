library(RPostgreSQL)
driver <- PostgreSQL()
con <- dbConnect(driver, host='localhost', dbname='econometrika', user='econometrika', password='^}jy5nnr(fVXK/Fw')

stmt <- dbSendQuery(con, "select * from analysis_split order by date desc")
splits <- fetch(stmt, -1)
dbClearResult(stmt)

#stmt <- dbSendQuery(con, "select * from analysis_symbol")
#symbols <- fetch(stmt, -1)
#symbols <- data.frame(id=110, ticker='REE', name='Red Eléctrica', market='MC')
#symbols <- data.frame(id=24, ticker='BKIA', name='BANKIA', market='MC')
symbols <- data.frame(id=91, ticker='MCM', name='MIQUEL Y COSTAS & MIQUEL', market='MC')
#dbClearResult(stmt)

library(plotly)
library(TTR)
library(xts)
libpath <- file.path(getwd(), './analysis/static/analysis/plotly_lib')
bpath <- './analysis/static/analysis/'
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
    bbands <- BBands(quotes[, c('High', 'Low', 'Close')], 50, sd=2.1)
    rsi <- RSI(quotes[, c('Close')])
    quotes <- cbind(quotes, bbands, rsi)
    quotes <- as.data.frame(quotes)
    btns <- list(
        list(
            count = 3, 
            label = "3M", 
            step = "month",
            stepmode = "backward"
        ), list(
            count = 6, 
            label = "6M", 
            step = "month",
            stepmode = "backward"
        ), list(
            count = 1, 
            label = "1A", 
            step = "year",
            stepmode = "backward"
        ), list(
            count = 3, 
            label = "3A", 
            step = "year",
            stepmode = "backward"
        ), list(
            count = 5, 
            label = "5A", 
            step = "year",
            stepmode = "backward"
        ), list(
            step = "all", label="Todo"
    ))

    p1 <- quotes %>%
        plot_ly(x = ~date, y = ~Close, type="scatter", mode="lines", name="Cierre") %>%
        add_lines(y = ~up , name = "B. Bollinger (50)",
                  line = list(color = '#bbb', width = 0.5),
                  legendgroup = "Bollinger Bands",
                  hoverinfo = "none") %>%
        add_lines(y = ~dn, name = "B. Bollinger (50)",
                  line = list(color = '#bbb', width = 0.5),
                  legendgroup = "Bollinger Bands",
                  showlegend = FALSE, hoverinfo = "none") %>%
        add_lines(y = ~mavg, name = "Media móvil (50)",
                  line = list(color = '#E377C2', width = 0.5),
                  hoverinfo = "none") %>%
        layout(title=tail(date, 1), yaxis = list(color = "#B3a78c", title="Cierre"), xaxis=list(rangeselector = list(x = 0, y = 1, buttons = btns, bgcolor = "#b3a78c", font=list(color="#1e2022"))))

    # plot volume bar chart
    p2 <- quotes %>%
        plot_ly(x=~date, y=~Volume, type='bar', name = "Volumen") %>% #,
                #color = ~direction, colors = c('#17BECF','#7F7F7F')) %>%
        layout(yaxis = list(color = "b3a78c", title = "Volumen"))

    p3 <- quotes %>%
        plot_ly(x=~date, y = ~EMA, name = "RSI (14)", type="scatter", mode="lines",
                  line = list(color = '#53e752', width = 1),
                  hoverinfo = "none") %>%
        layout(yaxis = list(color = "#B3a78c", title = "RSI"))

    ply <- subplot(p1, p2, p3, heights = c(0.65, 0.15, 0.15), nrows=3,
                   shareX = TRUE, titleY = TRUE) %>%
        layout(title = paste0('[', tail(quotes$Close, 1), '] ', symbol$name, ' (cotización ajustada): ', head(date, 1), ' - ' , tail(date, 1)),
               margin = list(t=50),
               font = list(color = "#B3A78C"),
               paper_bgcolor = '#1E2022',
               plot_bgcolor = '#3e3e3e',
               legend = list(orientation = 'h', x = 0.5, y = 1.02,
                             xanchor = 'center', yref = 'paper',
                             font = list(size = 10),
                             bgcolor = 'transparent'))

    slug <- paste0(tolower(symbol$ticker), '-adjusted-quote')
    wpath <- file.path(getwd(), bpath, paste0(slug, '.html'))
    htmlwidgets::saveWidget(ply, wpath, libdir=libpath, selfcontained=F)
    stmt <- postgresqlExecStatement(con, 'delete from analysis_plot where slug = $1', slug)
    dbClearResult(stmt)
    stmt <- postgresqlExecStatement(con, 'insert into analysis_plot (file_path, slug, title, lang_code_id, symbol_id, type, html_above) values ($1, $2, $3, $4, $5, $6, $7)',
        c(wpath, slug, paste0(symbol$name, ': cotización ajustada'), 'es', symbol$id, 'quote', ''))
    dbClearResult(stmt)
    print(paste0('Done with ', symbol$name))
}
dbDisconnect(con)
