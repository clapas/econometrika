library(RPostgreSQL)
driver <- PostgreSQL()
con <- dbConnect(driver, host='localhost', dbname='econometrika', user='econometrika', password='^}jy5nnr(fVXK/Fw')

stmt <- dbSendQuery(con, "select * from analysis_symbol")
symbols <- fetch(stmt, -1)
#symbols <- data.frame(id=3, ticker='rep', name='Repsol', market='MC')
dbClearResult(stmt)

library(plotly)
library(TTR)
library(xts)
libpath <- file.path(getwd(), './analysis/static/analysis/plotly_lib')
bpath <- './analysis/static/analysis/'
for (rs in rownames(symbols)) {
    symbol <- symbols[rs,]
    print(paste0('Generating for ', symbol$name))
    stmt <- dbSendQuery(con, "select sq.* from analysis_stockquote sq where sq.symbol_id  = $1 order by date", symbol$id)
    stock <- fetch(stmt, -1)
    dbClearResult(stmt)
    if (nrow(stock) == 0) next
    stmt <- dbSendQuery(con, "select d.* from analysis_dividend d where d.symbol_id = $1 order by ex_date desc", symbol$id)
    dividends <- fetch(stmt, -1)
    dbClearResult(stmt)
    for (r in rownames(dividends)) {
        dividend <- dividends[r,]
        ex_date <- dividend$ex_date
        ex_date_index <- NA
        j <- 0
        if (ex_date > tail(stock, 1)$date) next
        while (is.na(ex_date_index)) {
            ex_date_index <- match(ex_date + j, stock$date)
            j <- j + 1
        }
        m <- stock$close[ex_date_index] / (stock$close[ex_date_index] + dividend$gross)
        stock$close <- c(round(stock$close[stock$date < ex_date] * m, 3), stock$close[stock$date >= ex_date])
        stock$low <- c(round(stock$low[stock$date < ex_date] * m, 3), stock$low[stock$date >= ex_date])
        stock$high <- c(round(stock$high[stock$date < ex_date] * m, 3), stock$high[stock$date >= ex_date])
    }
    date <- stock$date
    stock <- xts(stock[, c('open', 'high', 'low', 'close', 'volume')], stock$date)
    colnames(stock) <- c('Open', 'High', 'Low', 'Close', 'Volume')
    bbands <- BBands(stock[, c('High', 'Low', 'Close')], 50, sd=2.1)
    rsi <- RSI(stock[, c('Close')])
    stock <- cbind(stock, bbands, rsi)
    stock <- as.data.frame(stock)
    p1 <- stock %>%
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
        layout(yaxis = list(color = "#B3a78c", title="Cierre"))

    # plot volume bar chart
    p2 <- stock %>%
        plot_ly(x=~date, y=~Volume, type='bar', name = "Volumen") %>% #,
                #color = ~direction, colors = c('#17BECF','#7F7F7F')) %>%
        layout(yaxis = list(color = "b3a78c", title = "Volumen"))

    p3 <- stock %>%
        plot_ly(x=~date, y = ~EMA, name = "RSI (14)", type="scatter", mode="lines",
                  line = list(color = '#53e752', width = 1),
                  hoverinfo = "none") %>%
        layout(yaxis = list(color = "#B3a78c", title = "RSI"))

    ply <- subplot(p1, p2, p3, heights = c(0.65, 0.15, 0.15), nrows=3,
                   shareX = TRUE, titleY = TRUE) %>%
        layout(title = paste0(symbol$name, ' (cotización ajustada): ', head(date, 1), ' - ' , tail(date, 1)),
               margin = list(t=50),
               font = list(color = "#B3A78C"),
               paper_bgcolor = '#1E2022',
               plot_bgcolor = '#3e3e3e',
               legend = list(orientation = 'h', x = 0.5, y = 1.02,
                             xanchor = 'center', yref = 'paper',
                             font = list(size = 10),
                             bgcolor = 'transparent'))

    wpath <- file.path(getwd(), bpath, paste0(symbol$ticker, '-adjusted-quote', '.html'))
    htmlwidgets::saveWidget(ply, wpath, libdir=libpath, selfcontained=F)
    print(paste0('Done with ', symbol$name))
}
dbDisconnect(con)
