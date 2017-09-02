create view price_to_book as
    select
            sh.n_shares,
            q.symbol_id,
            q.date, close_unadj,
            round((close_unadj / (capital_share * amount / sh.n_shares))::numeric, 3) as p2b
        from analysis_symbolquote q join (
            select symbol_id, max(date) as date 
                from analysis_symbolquote 
                group by symbol_id, date_trunc('quarter', date)) quarter_close
                    on quarter_close.date = q.date and quarter_close.symbol_id = q.symbol_id join 
            analysis_financialcontext ctx
                on date_trunc('quarter', ctx.period_end) = date_trunc('quarter', q.date) and
                    q.symbol_id = ctx.symbol_id -- root_concept_id (name = 'Balance consolidado')
                    join
            analysis_symbolnshares sh on (extract(year from sh.date) = extract(year from period_end) and sh.symbol_id = ctx.symbol_id) join
            analysis_financialfact ff on (ff.context_id = ctx.id) join
            analysis_financialconcept fc on (fc.id = ff.concept_id)
        where xbrl_element in (
            'ifrs-gp:EquityAttributableToEquityHoldersOfParent',
            'ipp-mas-pat:PatrimonioAtribuidoTenedoresInstrumentosPatrimonioNetoDominante',
            'ipp_se:I1189',
            'ipp_ge:I1189',
            'ipp_en:I1450',
            'es-be-fs:TotalPatrimonioNeto')
        group by q.symbol_id, capital_share, sh.n_shares, ff.id, q.date, close_unadj, amount
        order by q.symbol_id, q.date;
