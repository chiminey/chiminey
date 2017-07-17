// mutual exclusion [PZ82]
// dxp/gxn 19/12/99

probabilistic

// atomic formula
// none in low, high, tie
formula none_lht = (p2<4 | p2>13);

// some in admit
formula some_a	 = (p2>=14 & p2<=15);

// some in high, admit
formula some_ha	 = (p2>=4 & p2<=5) | (p2>=10 & p2<=15);

// none in high, tie, admit
formula none_hta = ((p2>=0 & p2<=3) | (p2>=7 & p2<=8));

// none in enter
formula none_e	 = (p2<2 | p2>3);

//param float highA;
//param float highA;
const double highA;
const double highB;

module process1

	p1: [0..15];
	
	[] p1=0 -> 0.5 : (p1'=0) + 0.5 : (p1'=1);
//	[] p1=0 -> (p1'=1);
	[] p1=1 -> (p1'=2);
	[] p1=2 &  (none_lht | some_a) -> (p1'=3);
	[] p1=2 & !(none_lht | some_a) -> (p1'=2);
	[] p1=3 -> (p1'=4);
	[] p1=3 -> (p1'=7);
	[] p1=4 &  some_ha -> (p1'=5);
	[] p1=4 & !some_ha -> (p1'=10);
	[] p1=5 -> (p1'=6);
	[] p1=6 &  some_ha -> (p1'=6);
	[] p1=6 & !some_ha -> (p1'=9);
	[] p1=7 &  none_hta -> (p1'=8);
	[] p1=7 & !none_hta -> (p1'=7);
	[] p1=8  -> (p1'=9);
	[toss1] p1=9  -> highA : (p1'=4) + 1-highA : (p1'=7);
	[] p1=10 -> (p1'=11);
	[] p1=11 &  none_lht -> (p1'=13);
	[] p1=11 & !none_lht -> (p1'=12);
	[] p1=12 -> (p1'=0);
	[] p1=13 -> (p1'=14);
	[] p1=14 &  none_e -> (p1'=15);
	[] p1=14 & !none_e -> (p1'=14);
	[] p1=15 -> (p1'=0);
	
endmodule

// construct further modules through renaming

module process2 = process1 [p1=p2, p2=p1, highA=highB, toss1=toss2] endmodule

rewards
//p1=9 | p2=9 : 1;
[toss1] true : 1;
[toss2] true : 1;
endrewards
