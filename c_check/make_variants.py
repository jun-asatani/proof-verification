"""Generate the instrumented / ablated variants of ilifc_core.c into ./build/.
ilifc_core.c has the same logic as the conference-version program ilifc.c
(created December 2013); only comments and variable names differ.
Variants:
  ilifc_log.c    - logs (kind, i, state before, state after) for every write
  ilifc_noE2c.c  - write_max phase (E2c) removed        (= CIL-ILIFC in practice)
  ilifc_noE2a.c  - write_alone phase (E2a) removed, E2c kept
  ilifc_E2clast.c- E2c moved after write_new (E2d)
"""
import os
t = open("ilifc_core.c").read()
os.makedirs("build", exist_ok=True)

E2A = """    for(j=1; j<=m; j++) {
      if(read_alone(j) && (read_maxi(j,k)%2)==(i%2)) {
	write_alone(j,i);
	write_num++;
	a=1;
	break;
      }
    }
    if(a==1) continue;
"""
E2C = """    for(j=1; j<=m; j++) {
      if(read_maxnum(j,k) && read_maxi(j,k)==i) {
	write_max(j,i);
	write_num++;
	a=1;
	break;
      }
    }
    if(a==1) continue;
"""
assert t.count(E2A) == 1 and t.count(E2C) == 1
open("build/ilifc_noE2c.c", "w").write(t.replace(E2C, ""))
open("build/ilifc_noE2a.c", "w").write(t.replace(E2A, ""))
last = t.replace(E2C, "").replace("    break;\n  }\n  return write_num;", E2C + "    break;\n  }\n  return write_num;")
assert last != t.replace(E2C, "")
open("build/ilifc_E2clast.c", "w").write(last)

head, body = t.split("int sim(int m, int k, int q)\n", 1)
for call, name in [("write_alone(j,i);", "A"), ("write(j,k,i);", "W"), ("write_change(j,i);", "C"),
                   ("write_max(j,i);", "M"), ("write_new(j,i);", "N")]:
    assert body.count(call) == 1, call
    body = body.replace(call, "LOGPRE('%s',j,i,k); %s LOGPOST(j,k);" % (name, call))
macros = r'''
static FILE *lg;
#define LOGPRE(c,j,i,k) do{ fprintf(lg,"%c %d ",c,i); for(int _n=1;_n<=k;_n++) fprintf(lg,"%d",x[j][_n]); }while(0)
#define LOGPOST(j,k) do{ fprintf(lg," "); for(int _n=1;_n<=k;_n++) fprintf(lg,"%d",x[j][_n]); fprintf(lg,"\n"); }while(0)
'''
head = head.replace("int x[MAX_m][MAX_k];", "int x[MAX_m][MAX_k];" + macros)
head = head.replace("init_genrand(1);", 'init_genrand(1); lg=fopen(getenv("LOGF"),"w");')
open("build/ilifc_log.c", "w").write(head + "int sim(int m, int k, int q)\n" + body)
