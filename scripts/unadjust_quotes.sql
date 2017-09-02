--select q.*, coalesce(exp(sum(ln(m))), 1) as am
--    from analysis_symbolquote q left join (
--        select q.*, q.close / (q.close + gross) as m
--            from analysis_symbolquote q join (
--                select symbol_id, gross, min(date) 
--                    from (
--                        select d.symbol_id, gross, date 
--                            from analysis_dividend d join analysis_symbolquote q
--                                on d.symbol_id = q.symbol_id and
--                                    d.ex_date <= q.date) p 
--                            group by symbol_id, gross) exq
--                on q.symbol_id = exq.symbol_id and q.date = exq.min) qm
--        on qm.date > q.date and qm.symbol_id = q.symbol_id
--    where q.symbol_id = 86
--    group by q.id 
--    order by date;

update analysis_symbolquote
    set close_unadj = round((close * dm * sm)::numeric, 3)
    from (
        select dq.id, dm, 1/coalesce(exp(sum(ln(proportion))), 1) as sm
            from (
                select q.*, 1/coalesce(exp(sum(ln(m))), 1) as dm
                    from analysis_symbolquote q left join (
                        select q.*, q.close / (q.close + gross) as m
                            from analysis_symbolquote q join (
                                select symbol_id, gross, min(date) 
                                    from (
                                        select d.id as dividend_id, d.symbol_id, gross, date 
                                            from analysis_dividend d join analysis_symbolquote q
                                                on d.symbol_id = q.symbol_id and
                                                    d.ex_date <= q.date) p 
                                            group by symbol_id, gross, dividend_id) exq
                                on q.symbol_id = exq.symbol_id and q.date = exq.min) qm
                        on qm.date > q.date and qm.symbol_id = q.symbol_id
                    group by q.id) dq left join
                analysis_split s on s.symbol_id = dq.symbol_id and s.date > dq.date
            --where dq.symbol_id = 86
            group by dq.id, dm) adj
    where analysis_symbolquote.id = adj.id;

--select dq.date, close, dq.symbol_id, dm, 1/coalesce(exp(sum(ln(proportion))), 1) as sm
--    from (
--        select q.*, 1/coalesce(exp(sum(ln(m))), 1) as dm
--            from analysis_symbolquote q left join (
--                select q.*, q.close / (q.close + gross) as m
--                    from analysis_symbolquote q join (
--                        select symbol_id, gross, min(date) 
--                            from (
--                                select d.id as dividend_id, d.symbol_id, gross, date 
--                                    from analysis_dividend d join analysis_symbolquote q
--                                        on d.symbol_id = q.symbol_id and
--                                            d.ex_date <= q.date) p 
--                                    group by symbol_id, gross, dividend_id) exq
--                        on q.symbol_id = exq.symbol_id and q.date = exq.min) qm
--                on qm.date > q.date and qm.symbol_id = q.symbol_id
--            group by q.id 
--            order by date) dq left join
--        analysis_split s on s.symbol_id = dq.symbol_id and s.date > dq.date
--    where dq.symbol_id = 86
--    group by dq.date, close, dq.symbol_id, dm
--    order by dq.date;
