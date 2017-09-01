        for symbol in symbols:
            ctxs = FinancialContext.objects.filter(symbol=symbol).order_by('period_end')
            # for each context having n_shares, assign it to all those newer contexts that still don't have it set
            for ctx in ctxs:
                if not ctx.n_shares: continue
                ctxs2 = FinancialContext.objects.filter(symbol=symbol, n_shares__isnull=True, period_end__lte=ctx.period_end)
                for ctx2 in ctxs2:
                    print('setting n_shares to context %s' % ctx2.id)
                    ctx2.n_shares = ctx.n_shares
                    ctx2.save()
            # for those still missing n_shares, set it to that of the newest financial context which already has n_shares calculated
            ctxs = FinancialContext.objects.filter(symbol=symbol).order_by('period_end')
            try:
                ctx = FinancialContext.objects.filter(symbol=symbol, n_shares__isnull=False).order_by('-period_end')[0]
                for ctx2 in ctxs:
                    if not ctx2.n_shares:
                        print('setting n_shares to context %s' % ctx2.id)
                        ctx2.n_shares = ctx.n_shares
                        ctx2.save()
            except:
                pass

            ctxs = FinancialContext.objects.filter(symbol=symbol).order_by('-period_end')
            for ctx in ctxs:
                try:
                    ctx_next = FinancialContext.objects.filter(symbol=ctx.symbol, n_shares__isnull=False, period_end__gte=ctx.period_end) \
                        .exclude(Q(n_shares=ctx.n_shares) | Q(id=ctx.id)).order_by('period_end')[0]
                    ctx_prev = FinancialContext.objects.filter(symbol=ctx.symbol, n_shares__isnull=False, period_end__lte=ctx.period_end) \
                        .exclude(Q(n_shares=ctx.n_shares) | Q(id=ctx_next.id) | Q(id=ctx.id)).order_by('-period_end')[0]
                    if (ctx_next.n_shares > ctx.n_shares and ctx_prev.n_shares > ctx.n_shares or \
                        ctx_next.n_shares < ctx.n_shares and ctx_prev.n_shares < ctx.n_shares) and \
                        abs(1 - ctx.n_shares / ctx_next.n_shares) >= NSHARES_EQ_EPSILON and \
                        abs(1 - ctx.n_shares / ctx_prev.n_shares) >= NSHARES_EQ_EPSILON and \
                        abs(1 - ctx_prev.n_shares / ctx_next.n_shares) < NSHARES_EQ_EPSILON:
                        nshares = round((ctx_prev.n_shares + ctx_prev.n_shares) / 2)
                        print('    correcting n_shares for %s (%s - %s), from %s to %s' % (ctx.report_type, ctx.period_begin, ctx.period_end, ctx.n_shares, nshares))
                        ctx.n_shares = nshares
                        ctx.save()
                except Exception as e:
                    pass



