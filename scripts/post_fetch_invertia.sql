update analysis_symbolquote set volume = high, high = greatest(open, low, close) from analysis_symbol sy where sy.id = analysis_symbolquote.symbol_id and ticker = 'REE' and date <= '2001-12-28';

update analysis_symbolquote set high = low, low = high from analysis_symbol sy where sy.id = analysis_symbolquote.symbol_id and ticker in ('ZOT', 'VID') and high < low ;
update analysis_symbolquote set high = close from analysis_symbol sy where sy.id = analysis_symbolquote.symbol_id and ticker in ('ZOT', 'VID') and high < close ;
update analysis_symbolquote set high = open from analysis_symbol sy where sy.id = analysis_symbolquote.symbol_id and ticker in ('ZOT', 'VID') and high < open;
update analysis_symbolquote set low = close from analysis_symbol sy where sy.id = analysis_symbolquote.symbol_id and ticker in ('ZOT', 'VID') and low > close ;
update analysis_symbolquote set low = open from analysis_symbol sy where sy.id = analysis_symbolquote.symbol_id and ticker in ('ZOT', 'VID') and low > open;
