--select year, symbol_id, nominal/coalesce(exp(sum(ln(proportion))), 1)
--    from (
--        select sy.year, sy.id as symbol_id, nominal, proportion
--            from (
--                select *
--                    from generate_series(2004, 2017, 1) year cross join analysis_symbol) sy left join
--                analysis_split sp on sy.id = sp.symbol_id and extract(year from sp.date) > sy.year) sysp
--    group by year, symbol_id, nominal
--    order by symbol_id, year;
--

--select year, symbol_id, nominal/coalesce(exp(sum(ln(proportion))), 1)--, capital
--    from (
--        select extract(year from period_end) as year, ctx.symbol_id as symbol_id, nominal, proportion--, amount as capital
--            from analysis_financialcontext ctx join
--                --analysis_financialfact ff on ctx.id = ff.context_id join
--                --analysis_financialconcept fc on (fc.id = ff.concept_id) join
--                analysis_symbol sy on ctx.symbol_id = sy.id left join
--                analysis_split sp on ctx.symbol_id = sp.symbol_id and extract(year from sp.date) > extract(year from period_end)
--            --where xbrl_element in (
--            --    'es-be-fs:CapitalfondoDotacion',
--            --    'ipp-mas-pat:CapitalNIIF',
--            --    'ipp_en:I1281',
--            --    'ipp_ge:I1161',
--            --    'ipp_se:I1161')
--            --group by ctx.symbol_id, extract(year from period_end), nominal, proportion, capital) sysp where symbol_id = 119
--            group by ctx.symbol_id, extract(year from period_end), nominal, proportion) sysp where symbol_id = 119
--    group by year, symbol_id, nominal
--    order by symbol_id, year;

select year, symbol_id, nominal/coalesce(exp(sum(ln(proportion))), 1) as nominal_adj, capital, capital / (nominal/coalesce(exp(sum(ln(proportion))), 1)) as nshares
    from (
        select extract(year from period_end) as year, ctx.symbol_id as symbol_id, nominal, proportion, min(amount) as capital
            from analysis_financialcontext ctx join
                analysis_financialfact ff on ctx.id = ff.context_id join
                analysis_financialconcept fc on (fc.id = ff.concept_id) join
                analysis_symbol sy on ctx.symbol_id = sy.id left join
                analysis_split sp on ctx.symbol_id = sp.symbol_id and extract(year from sp.date) > extract(year from period_end)
            where xbrl_element in (
                'es-be-fs:CapitalFondoDotacion',
                'ipp-mas-pat:CapitalNIIF',
                'ipp_en:I1281',
                'ipp_ge:I1161',
                'ipp_se:I1161')
            group by ctx.symbol_id, extract(year from period_end), nominal, proportion) sysp where symbol_id = 119
    group by year, symbol_id, nominal, capital
    order by symbol_id, year;
