// Developed by Ahmed Abdullah,
// AICAUSE Lab, RMIT Universiy. November 2016

dtmc

const double p;
const double d;
const double e;

module main
  s: [-1..2] init 0;

  [] s=-1 -> (s'=-1);
  [] s=0 -> d   : (s'=-1) + p : (s'=1) + 1-d-p: (s'=0);
  [] s=1 -> 1-e : (s'=0) + e  : (s'=2);
  [] s=2 -> (s'=2);

endmodule

rewards
  true : 1;
endrewards
