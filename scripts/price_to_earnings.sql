create view price_to_earnings as
    select
            sh.n_shares,
            q.symbol_id,
            q.date,
            round((close_unadj / (capital_share * amount / sh.n_shares))::numeric, 3) as per
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
            'ipp_en:I1572', -- 2016 en
            'ipp_ge:I1300', -- 2016 ge
            'ipp_se:I1300', -- 2016 se
            'ifrs-gp:ProfitLossAttributableToEquityHoldersOfParent', -- 2008 en
            'ifrs-gp:ProfitLossAttributableToEquityHoldersOfParent', -- 2008 ge
            'ifrs-gp:ProfitLossAttributableToEquityHoldersOfParent', -- 2008 se
            'ifrs-gp:ProfitLossAttributableToEquityHoldersOfParent', -- 2005 en
            'ipp-mas-pat:BeneficioPerdidaAtribuibleTenedoresInstrumentosPatrimonioNetoDominante', -- 2005 ge
            'ipp-mas-pat:BeneficioPerdidaAtribuibleTenedoresInstrumentosPatrimonioNetoDominante') and -- 2005 se
            amount <> 0
        group by q.symbol_id, capital_share, sh.n_shares, ff.id, q.date, close_unadj, amount
        order by q.symbol_id, q.date;

