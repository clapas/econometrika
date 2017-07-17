library(RPostgreSQL)
driver <- PostgreSQL()
con <- dbConnect(driver, host='localhost', dbname='econometrika', user='econometrika', password='^}jy5nnr(fVXK/Fw')

stmt <- dbSendQuery(con, "select * from analysis_symbol")
symbols <- fetch(stmt, -1)
dbClearResult(stmt)

library(plotly)
libpath <- file.path(getwd(), './analysis/static/analysis/plotly_lib')
bpath <- 
for (rs in rownames(symbols)) {
    symbol <- symbols[rs,]
    stmt <- dbSendQuery(con, "select sq.* from analysis_stockquote sq where sq.symbol_id  = $1 order by date", symbol$id)
    stock <- fetch(stmt, -1)
    dbClearResult(stmt)
    if (nrow(stock) == 0) next
    stmt <- dbSendQuery(con, "select d.* from analysis_dividend d where d.symbol_id = $1 order by ex_date", symbol$id)
    dividends <- fetch(stmt, -1)
    dbClearResult(stmt)
    stock$close_adj <- stock$close
    for (r in rev(rownames(dividends))) {
        dividend <- dividends[r,]
        ex_date <- dividend$ex_date
        ex_date_index <- NA
        j <- 0
        while (is.na(ex_date_index)) {
            ex_date_index <- match(ex_date + j, stock$date)
            j <- j + 1
        }
        m <- stock$close_adj[ex_date_index] / (stock$close_adj[ex_date_index] + dividend$gross)
        stock$close_adj <- c(stock$close_adj[stock$date < ex_date] * m, stock$close_adj[stock$date >= ex_date])
    }
    p <- ggplot(stock, aes(x=date, y=close_adj, group=1, text=paste('Date: ', date, '\nAdj. Close: ', round(close_adj, 3), sep=''))) + geom_line(size=0.3) + ggtitle(paste0(symbol$name, ' (cotización ajustada por dividendos)'))
    ply <- ggplotly(p, tooltip='text')
    wpath <- file.path(getwd(), './analysis/static/analysis/', paste0(symbol$ticker, '-adjusted-quote', '.html'))
    htmlwidgets::saveWidget(ply, wpath, libdir=libpath, selfcontained=F)
}
