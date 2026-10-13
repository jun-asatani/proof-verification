/* minimal MT19937 (reference algorithm, Matsumoto & Nishimura) */
#include <stdint.h>
static uint32_t mt[624]; static int mti=625;
static void init_genrand(uint32_t s){ mt[0]=s; for(mti=1;mti<624;mti++) mt[mti]=(1812433253U*(mt[mti-1]^(mt[mti-1]>>30))+mti); }
static uint32_t genrand_int32(void){ uint32_t y; static uint32_t mag01[2]={0x0,0x9908b0dfU};
 if(mti>=624){ int kk; if(mti==625) init_genrand(5489U);
  for(kk=0;kk<624-397;kk++){ y=(mt[kk]&0x80000000U)|(mt[kk+1]&0x7fffffffU); mt[kk]=mt[kk+397]^(y>>1)^mag01[y&1]; }
  for(;kk<623;kk++){ y=(mt[kk]&0x80000000U)|(mt[kk+1]&0x7fffffffU); mt[kk]=mt[kk+(397-624)]^(y>>1)^mag01[y&1]; }
  y=(mt[623]&0x80000000U)|(mt[0]&0x7fffffffU); mt[623]=mt[396]^(y>>1)^mag01[y&1]; mti=0; }
 y=mt[mti++]; y^=(y>>11); y^=(y<<7)&0x9d2c5680U; y^=(y<<15)&0xefc60000U; y^=(y>>18); return y; }
static double genrand_real2(void){ return genrand_int32()*(1.0/4294967296.0); }
