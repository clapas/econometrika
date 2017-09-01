select ctx.n_shares_calc, q.symbol_id, q.date, close, round(((close/(amount/(ctx.n_shares_calc)))/coalesce(exp(sum(ln(s.proportion))), 1))::numeric, 3) as p2b
    from analysis_symbolquote q join (
--        select max(date) as date 
--            from analysis_symbolquote 
--            where symbol_id = 23 -- oldest symbol, SAN
--            group by date_trunc('quarter', date)) quarter_close
--                on quarter_close.date = q.date join 
        select symbol_id, max(date) as date 
            from analysis_symbolquote 
            group by symbol_id, date_trunc('quarter', date)) quarter_close
                on quarter_close.date = q.date and quarter_close.symbol_id = q.symbol_id join 
        analysis_financialcontext ctx
            on date_trunc('quarter', ctx.period_end) = date_trunc('quarter', q.date) and
                q.symbol_id = ctx.symbol_id -- root_concept_id (name = 'Balance consolidado')
                join
        analysis_financialfact ff on (ff.context_id = ctx.id) join
        analysis_financialconcept fc on (fc.id = ff.concept_id) left join
        analysis_split s on s.symbol_id = q.symbol_id and extract(year from s.date) >= extract(year from q.date) -- split not accounted at balance sheet date
    where xbrl_element in (
        'ifrs-gp:EquityAttributableToEquityHoldersOfParent',
        'ipp-mas-pat:PatrimonioAtribuidoTenedoresInstrumentosPatrimonioNetoDominante',
        'ipp_se:I1189',
        'ipp_ge:I1189',
        'ipp_en:I1450',
        'es-be-fs:TotalPatrimonioNeto')
    group by q.symbol_id, ctx.n_shares_calc, ff.id, q.date, close, amount
    order by q.symbol_id, q.date;

