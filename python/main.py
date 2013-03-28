#!/usr/bin/env python
# -*- coding: utf-8 -*-
import cPickle as pickle
import connection
from colors import good, bad, info


class config(object):
    datafile = 'data'
#    host = 'universum.dl24'
#    port = '20003'
    dontload = "reset"

def getparam(param):
    for arg in args:
        if arg.startswith(param):
            return int(arg.split('=')[1])
    return None

class serializator(object):
    @staticmethod 
    def load():
        global orders,done,impossible
        if config.dontload in args:
            new_world()
        else:
            print info("wczytuję...")
            f = file(config.datafile, 'r')
            orders,done,impossible = pickle.load(f)
            f.close()
    
    @staticmethod
    def save():
        print info("zapisuję...")
        f = file(config.datafile, 'w')
        global orders, done
        pickle.dump((orders,done,impossible), f, protocol=2)
        f.close()

skipped = set()

class order(object):
    def __init__(self, oid):
        self.id = oid
        print "getting order %d" %self.id
        self.read()

    def read(self):
        conn.cmd("describe_order %d" % self.id)
        self.n = conn.readint()
        self.m = conn.readint()
        self.value = conn.readfloat()
        self.teams = conn.readint()
        
        
        self.G = [[] for _ in xrange(self.n+1)]
        for _ in xrange(self.m):
            a,b = conn.readint(), conn.readint()
            self.G[a].append(b)
            self.G[b].append(a)
    
    def __str__(self):
        return "#%d\t(%d %d %f %d)\ttimeout=%d" % (self.id, self.n, self.m, self.value, self.teams, self.lasttimeout)
    
    def dfs(self, u=0):
        if not u:
            self.dfsorder = []
            self.dfs(1)
            self.compute_dfsno()
        else:
            self.dfsorder.append(u)
            for v in self.G[u]:
                if v not in self.dfsorder:
                    self.dfs(v) 
    
    def compute_dfsno(self):
        self.dfsno = [0 for _ in xrange(0,self.n+1)]
        for i,v in enumerate(self.dfsorder):
            self.dfsno[v] = i
    
    def dfs2(self):
        leftlist = sorted(range(1,self.n+1), key=lambda u: len(self.G[u]))
        self.dfsorder = [leftlist.pop()]
        while leftlist:
            leftlist.sort(key=lambda u: len([v for v in self.dfsorder if u in self.G[v]]))
            self.dfsorder.append(leftlist.pop())
        self.compute_dfsno()
    
    def is_done(self):
        if self.id in done: return True
        return self.commit(range(1,self.n+2))
    
    @staticmethod
    def fully_zawiera(lw, lm):
        if len(lw) < len(lm): return False
        lw.sort(reverse=True)
        lm.sort(reverse=True)
        for w,m in zip(lw,lm):
            if w<m:
                #print bad(str(lw) + str(lm)) 
                return False
        return True
    
    def __getattr__(self, name):
        if name == 'lasttimeout':
            self.lasttimeout = int((10000 / 50 ) * self.value) 
            return self.lasttimeout
        else:
            raise AttributeError
    
    def match(self):
        #if self.is_done():
        #    print info("already matched")
        #    return
        global skipped, impossible
        to = [0 for _ in xrange(self.n+1)]
        left_v = set(range(1,n+1))
        self.timer = 0
        
        if not hasattr(self, 'dfsorder'):
            self.dfs()
        if not hasattr(self, 'Z'):
            self.Z = compute_Z2(self.G)
#        if not hasattr(self, 'lasttimeout'):
#            self.lasttimeout = time_limit
            
        print "matching #%d"%self.id, self.n
        
        def match_first(i):
            if i >= self.n:
                print "FOUND", self
                self.commit(to)
                return True
            else:
                u = self.dfsorder[i]
                curset = set(left_v)
                sparowani_sasiedzi = filter(lambda w: self.dfsno[w]<i, self.G[u])
                #for sas in sparowani_sasiedzi:
                #    curset.intersection_update(GS[to[sas]])
                curset.intersection_update(*[GS[to[sas]] for sas in sparowani_sasiedzi])
                
                
                for v in sorted(curset, key=lambda v: -len(G[v])):
                    # we want to map u to v
                    if len(G[v])<len(self.G[u]):
                        #print info("cut by len")
                        continue
                    if not self.fully_zawiera([len(G[vv]) for vv in G[v]], [len(self.G[uu]) for uu in self.G[u]]):
                        #print info("[z]"),
                        continue
                    
                    cutbyz=0
                    for odl in range(6):
                        if len(Z[odl][v])<len(self.Z[odl][u]):
                            #print info("cut by Z%d"%odl)
                            cutbyz=odl
                            break
                    if cutbyz:
                        continue

                    self.timer += 1
                    if self.timer>self.lasttimeout:#time_limit:
                        raise OverflowError
                    
                    
                    
                    to[u] = v
                    left_v.remove(v)
                    if match_first(i+1):
                        return True
                    else:
                        left_v.add(v)
        try:
            if not match_first(0):
                print "impossible"
                impossible.add(self.id)
        except OverflowError:
            print "timeout (%d)"%(self.lasttimeout), self
            skipped.add(self.id)
            self.lasttimeout *= 2
        del self.timer
    
    def commit(self, mapping):
        print self, mapping
        res = conn.cmd("commit_solution %d %d %s" % (self.id, self.n, ' '.join(map(str,mapping[1:]))))
        if res and res.startswith("FAILED 102 you have already answered this order"):
            done.add(self.id)
            return False
        else:
            line = conn.readline()
            if line.startswith("ACCEPTED"):
                print good(line)
                done.add(self.id)
                return True    
            else:
                print bad(line)
                return False

def new_world():
    global orders,done,impossible,skipped
    orders = []
    done = set()
    skipped = set()
    impossible = set()
    refresh_G()
    serializator.save()

def refresh_G():
    global G, GS, n,m,t,k, Z
    conn.cmd_describe_world()
    n,m,t,k = conn.readint(), conn.readint(), conn.readint(), conn.readfloat()
    print n,m,t,k
    G = [[] for _ in xrange(n+1)]
    GS = [set() for _ in G]
    for _ in xrange(m):
        a,b = conn.readint(), conn.readint()
        G[a].append(b)
        G[b].append(a)
        GS[a].add(b)
        GS[b].add(a)
    Z = compute_Z2(G)

def update_orders():
    oc = conn.order_count()
    limit = 40
    if oc<len(orders):
        new_world()
    for i in range(len(orders)+1, oc+1)[:limit]:
        orders.append(order(i))
    if oc>len(orders):
        conn.wait()
        update_orders()

def compute_Z2(Graf):
    Z = []
    Z.append([set([v]) for v in range(len(Graf))])
    for _ in range(1,6):
        Z.append([Z[-1][v].union(*[Z[-1][u] for u in Graf[v]]) for v in range(len(Graf))])
    return Z
#    return [set().union(*[Graf[v] for v in Graf[u]]) for u in range(len(Graf))]
    

#############################################################################
#############################################################################
#############################################################################
try:
    # connect to server
    args = connection.args()
    conn = connection.connection()
    print info("connected")
    #conn.login()
    print info("logged in")
  
    serializator.load()
    print len(orders), done
    print impossible
    
    time_limit = getparam("time")
    
    refresh_G()
    print info("G done")
    
#    for i in range(0,100):
#        print conn.order_count()
        
#    for o in orders:
#        if o.id == 315:
#            f = file("dump2", 'w')
#            print>>f, o.dfsorder
#            f.close() 

    
    lam = lambda o: (o.id in done, o.n, -o.value)    
    val_lam = lambda o: -o.value
    team_lam = lambda o: -o.teams
     
    main_loop_turn = 0
    while True:
        main_loop_turn += 1
        
        
        update_orders()
        
        if 'doall' in args:
            possible = filter(lambda o: o.id not in done and o.id not in impossible, orders)
        else:
            possible = filter(lambda o: o.id not in done and o.id not in impossible and o.teams>0, orders)
            
        if getparam('mod') is not None:
            mod = getparam('mod')
            possible = filter(lambda o:o.id%3==mod, possible)
        
        soror = sorted(possible, key=lam)
        if 'value' in args:
            soror = sorted(soror, key=val_lam)
        if 'easy' in args:
            soror = sorted(soror, key=team_lam)
        if 'ts' in args:
            soror = sorted(soror, key=lambda o: o.lasttimeout)
        
        print "lista", len(soror)
        for o in soror[:20]:
            print o

            
        if 'niszcz' in args:
            def first_not_skipped():
                global skipped, time_limit
                for i in xrange(len(soror)):
                    if soror[i].id not in done:
                        return i
                print info("resetting skipped")
                #skipped = set()
                #time_limit *= 3
                raise StopIteration
            try:
                soror[first_not_skipped()].match()
            except StopIteration:
                conn.wait()
        
        if not (main_loop_turn%20):
            serializator.save()
             
        if 'czekaj' in args: conn.wait()
        
        
        
        
        
        
        
        
    
    
        
    
        pass
except KeyboardInterrupt:
    pass
    serializator.save()    
#except Exception as e:
#    print type(e), e
#    if raw_input("wpisz [z], by zapisać: ") == 'z':
#        serializator.save()