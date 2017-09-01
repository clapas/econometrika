select sy.*, ss.key, last_div.date as last_div_date
    from analysis_symbol sy 
        join analysis_symbolsource ss on ss.symbol_id = sy.id 
        left join (
            select symbol_id, max(ex_date) as date
            from analysis_dividend
            group by symbol_id) as last_div on last_div.symbol_id = sy.id
    where ticker = 'TRE' and ss.name = 'quantmod' and ss.type = 'quote'
