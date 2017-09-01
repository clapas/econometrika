select *
    from (
        select extract(year from period_end) as year, symbol_id
            from analysis_financialcontext
            group by year, symbol_id) ctx right outer join (
        select ticker, name, id as symbol_id, x as year
            from generate_series(2004, 2017, 1) x cross join analysis_symbol) s on s.symbol_id = ctx.symbol_id and s.year = ctx.year
    where ctx.year is null
    order by s.symbol_id, s.year;
