# -*- coding:utf-8 -*-

import cProfile
import pstats

import benchmark # NOQA

cProfile.run('benchmark.test_sync(1000)', "prof.data")
p = pstats.Stats('prof.data')
p.sort_stats('cumulative')
p.print_stats()
