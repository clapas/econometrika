ibex35 <- read.csv('data/ibex35.csv')
ibex35$Rate <- c(0, log(tail(ibex35$Close, -1)/head(ibex35$Close, -1)))
library(plotly)
p <- ggplot(ibex35, aes(text=paste('Date: ', Date, '\n', 'Compounding rate: ', round(Rate, 4), '\n', 'Change: ', round(exp(Rate)-1, 4)*100, '%', sep=''))) + geom_segment(aes(x=as.Date(Date), y=0, yend=Rate, xend=as.Date(Date)), size=0.2) + labs(x='Día', y='Ratio', caption=paste('Ratio de composición diario del IBEX35 desde ', head(ibex35$Date, 1), ' hasta ', tail(ibex35$Date, 1))) + theme(plot.caption = element_text(hjust = 0.5))
ply <- ggplotly(p, tooltip='text')
libpath <- file.path(getwd(), './widgets/plotly_lib')
wpath <- file.path(getwd(), './widgets/ibex35-daily-rate.html')
htmlwidgets::saveWidget(ply, wpath, libdir=libpath, selfcontained=F)
ggsave('ibex35-daily-rate.png', p + theme(text = element_text(size=6)) + geom_text(hjust='right', data=subset(ibex35, Rate %in% c(min(Rate), max(Rate))), size=1.5, aes(x=as.Date(Date), y=Rate, label=paste(as.Date(Date), ': ', round(exp(Rate)*100-100, 2), '% ', sep=''))), 'png', 'widgets', height=55, units=c("mm"))

# gauusian distribution: theoric no. ocurrences of drop > 1%, 3%, 5%, etc
mdg <- mean(ibex35$Rate)
sdg <- sd(ibex35$Rate)
libex35 <- length(ibex35$Rate)
pnorm(log(0.99), mdg, sdg)*libex35
pnorm(log(0.97), mdg, sdg)*libex35
pnorm(log(0.95), mdg, sdg)*libex35
pnorm(log(0.93), mdg, sdg)*libex35
pnorm(log(0.91), mdg, sdg)*libex35
pnorm(log(0.89), mdg, sdg)*libex35
# actual no. ocurrences of drop > 1%, 2.5%, 5%, etc
sum(ibex35$Rate < log(0.99))
sum(ibex35$Rate < log(0.97))
sum(ibex35$Rate < log(0.95))
sum(ibex35$Rate < log(0.93))
sum(ibex35$Rate < log(0.91))
sum(ibex35$Rate < log(0.89))

p1 <- ggplot(ibex35, aes(Rate)) + geom_histogram(bins=300, aes(y=..density.., fill=..count..)) + stat_function(fun=dnorm, aes(colour="Normal distribution"), args=list(mean=mdg, sd=sdg)) + scale_fill_continuous(guide = guide_legend(title = "Ratio de composición diario del IBEX35")) + scale_colour_manual(name=NULL, values=c("red")) + theme(legend.position="top")
p2 <- ggplot(ibex35, aes(sample = Rate)) + stat_qq(color="orange", alpha=1) + geom_abline(intercept = mdg, slope = sdg)
sp <- subplot(p1, p2)
wpath <- file.path(getwd(), './widgets/ibex35-daily-rate-normality.html')
htmlwidgets::saveWidget(sp, wpath, libdir=libpath, selfcontained=F)
png('widgets/ibex35-daily-rate-normality.png', width=2100, units='px', height=649)
multiplot(p1 + theme(text = element_text(size=18)), p2 + theme(text = element_text(size=18)), cols=2)
dev.off()

mdl <- median(ibex35$Rate)
sdl <- mad(ibex35$Rate, constant=1)*sqrt(2)
library(rmutil)
p1 <- ggplot(ibex35, aes(Rate)) + geom_histogram(bins=300, aes(y=..density.., fill=..count..)) + stat_function(fun=dlaplace, aes(colour="Laplace distribution"), args=list(m=mdl, s=sdl)) + scale_fill_continuous(guide = guide_legend(title = "Ratio diario del IBEX35")) + scale_colour_manual(name=NULL, values=c("red")) + theme(legend.position="top")
p2 <- ggplot(ibex35, aes(sample = Rate)) + stat_qq(color="orange", alpha=1, distribution=qlaplace) + geom_abline(intercept = mdl, slope = sdl)
sp <- subplot(p1, p2)
wpath <- file.path(getwd(), './widgets/ibex35-daily-rate-laplacity.html')
htmlwidgets::saveWidget(sp, wpath, libdir=libpath, selfcontained=F)
png('widgets/ibex35-daily-rate-laplacity.png', width=2100, units='px', height=649)
multiplot(p1 + theme(text = element_text(size=18)), p2 + theme(text = element_text(size=18)), cols=2)
dev.off()

# laplace distribution: theoric no. ocurrences of drop > 1%, 2.5%, 5%, etc
plaplace(log(0.99), mdl, sdl)*libex35
plaplace(log(0.97), mdl, sdl)*libex35
plaplace(log(0.95), mdl, sdl)*libex35
plaplace(log(0.93), mdl, sdl)*libex35
plaplace(log(0.91), mdl, sdl)*libex35
plaplace(log(0.89), mdl, sdl)*libex35
