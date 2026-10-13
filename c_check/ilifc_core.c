#include <stdio.h>
#include <stdlib.h>
#include "mt.h"
#define MAX_m 101
#define MAX_k 101
#define Max_q 50
#define Max_write 500001
int x[MAX_m][MAX_k];

int sim(int m, int k, int q);
void write_new(int j, int i);
void write(int j, int k, int i);
int read_index(int j, int k, int q);
int active(int j, int k, int q);
int clear(int j, int k, int q);
int read_layer(int j, int k);
int read_maxi(int j, int k);
int read_maxnum(int j, int k);
int read_max(int j, int k);
void write_max(int j, int i);
int read_alone(int j);
void write_alone(int j, int i);
int parity(int j, int k);
void write_change(int j, int i);

int main(int argc, char *argv[])
{
  int n, k, q, m;
  int num_sim;
  char filename[60];
  FILE *fp;
  int num, write_num;
  double ave = 0.0;
  static int write_kei[Max_write]={0}; 
  if (argc != 6)
    {
      printf("Usage: %s  n, k, q, num_sim, filename\n", argv[0]);
      exit(0);
    }
  sscanf(argv[1],"%d", &n);
  sscanf(argv[2],"%d", &k);
  sscanf(argv[3],"%d", &q);
  sscanf(argv[4],"%d", &num_sim);
  sscanf(argv[5],"%s", filename);
    fp = fopen(filename, "w");
    m = n / k;
    init_genrand(1);
    for(num=0; num < num_sim; num++){
      write_num = sim(m,k,q);
      ave  += write_num;
      write_kei[write_num]++;
    }
    for(num= k*q-1; num <= n*(q-1); num++){
      fprintf(fp,"%d  %d\n", num, write_kei[num]);
    }
    printf("%.3f\n", ave/num_sim);
    fclose(fp);
    return 0;
}

int active(int j, int k, int q)
{
  int n, i;
  int s=0;
  int a=0;
  for(i=1; i<=k; i++){
    s  += x[j][i];
  }
  for(n=1; n<k; n++) {
    if(x[j][n] != x[j][n+1]) 
      a = 1;
  }
  if (s ==  k*(q-1) || a == 0)
    {
      return 0;
    }
  else
    {
      return 1;
    }  
}

int read_index(int j, int k, int q)
{  
  int n, i;
  int max;
  int a=0, s=0; 
  int index=0;
  for(n=1; n<k; n++) {
    if(x[j][n] != x[j][n+1]) 
      a = 1;
  }
  for(i=1; i<=k; i++){
    s += x[j][i];
  }
  if (s ==  k*(q-1) || a == 0)
    {
      index = 0;
      return index;
    } 
  max = x[j][1]-x[j][k];
  index = 1;
  for (n=2 ; n<=k; n++) {
    if ( max <   x[j][n]-x[j][n-1]) {
      max =  x[j][n]-x[j][n-1];
      index = n;
    }
  }
  return index;
}

void write(int j, int k, int i)
{
  int n; 
  int write_num;
  int y=0;
  for(n=1; n<=k; n++) {
    y += x[j][n];
  }
  write_num = (i + y) % k;
  if(write_num == 0)  write_num=k; 
  x[j][write_num]++;
}

void write_new(int j, int i)
{
  x[j][i]++;
}

int clear(int j, int k, int q)
{
  int n, a=1, s;
  for(n=1; n<k; n++) {
    if(x[j][n] != x[j][n+1]) 
      a = 0;
  }
  s=0;
  for(n=1; n<=k; n++){
    s += x[j][n];
  }
  if(s == k*(q-1))
    a=0;
  return a;
}

int read_layer(int j, int k)
{
  int n, max;
  max = x[j][1];
  for(n=2 ; n<=k; n++) {
    if(max < x[j][n]) {
      max = x[j][n];
    }
  }
  return max;
}

int read_maxi(int j, int k)
{
  int i_max=0;
  int n,  s=0;
  int max;
  max = read_max(j,k);
  for(n=1; n<=k; n++) {
    if(max == x[j][n])
      { 
	i_max = n;
	break;
      }
  }
  if (i_max == 1) s=3;
  if (i_max == 2) s=4;
  if (i_max == 3) s=1;
  if (i_max == 4) s=2;
  return s;
}

int read_maxnum(int j, int k)
{
  int max, n, a=0;
  max = read_max(j,k);
  for(n=1; n<=k; n++) {
    if(x[j][n] == max)
      a++;
  }
  if(a>1) a=0;
  return a;
}

int read_max(int j, int k)
{
  int max, n;
  max = x[j][1];
  for(n=2 ; n<=k; n++) {
    if(max < x[j][n]) {
      max = x[j][n];
    }
  }
  return max;
}

void write_max(int j, int i)
{
  x[j][i]++;
}

int read_alone(int j)
{
  int a=0;
  if(x[j][1]!=x[j][2] && x[j][3]!=x[j][4]) {
    if(x[j][1]==x[j][3] && x[j][2]==x[j][4]) {
      a=1;
    }
  }
  return a;
}

void write_alone(int j, int i)
{
  if(i==1) x[j][4]++;
  if(i==2) x[j][1]++;
  if(i==3) x[j][2]++;
  if(i==4) x[j][3]++;
}

int parity(int j, int k)
{
  int n, s=0;
  for(n=1; n<=k; n++){
    s = s+x[j][n];
  }
  s = s%2;
  return s;
}

void write_change(int j, int i)
{
  x[j][i]++;
}

int sim(int m, int k, int q)
{
  int L, R;
  for(L=1; L<=m; L++) {
    for(R=1; R<=k; R++) {
      x[L][R] = 0;
    }
  } 
  int j, i, l;
  int a;
  int write_num=0;
  while(1){
    a = 0;
    i = (int)(k*genrand_real2()+1);  
    for(j=1; j<=m; j++) {
      if(read_alone(j) && (read_maxi(j,k)%2)==(i%2)) {
	write_alone(j,i);
	write_num++;
	a=1;
	break;
      }
    }
    if(a==1) continue;
    for (j=1; j<=m; j++){
      if (active(j,k,q) && read_index(j,k,q) == i && read_alone(j)==0)
	{
	  write(j,k,i);
	  write_num++; 
	  a = 1;
	  break;
	}
    }
    if(a==1) continue;
    for(j=1; j<=m; j++) {
      if (read_index(j,k,q) == ((i%k)+1) && parity(j,k) == 0 && read_alone(j)==0) {
	write_change(j,i);
	write_num++;
	a=1;
	break;
      }
    }
    if(a==1) continue;
    for(j=1; j<=m; j++) {
      if(read_maxnum(j,k) && read_maxi(j,k)==i) {
	write_max(j,i);
	write_num++;
	a=1;
	break;
      }
    }
    if(a==1) continue;
    for(l=0; l<=q-1; l++) {
      for(j=1; j<=m; j++) {
	if(clear(j,k,q) && (read_layer(j,k)==l)) {
	  write_new(j,i);
	  write_num++;
	  a = 1;
	  break;
	}
      }
      if(a==1) break;
    }
    if(a==1) continue;
    break;
  }
  return write_num;
}
