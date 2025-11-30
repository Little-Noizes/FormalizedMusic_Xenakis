(
SynthDef(\upicSynth, { |freq = 440, amp = 0.5, gliss = 0.2, dens = 0.8|
    var env = EnvGen.kr(Env.perc(0.01, 0.3), doneAction: 2);
    var mod = LFNoise2.kr(dens * 10) * gliss * 100;
    var sig = SinOsc.ar(freq + mod, 0, amp) * env;
    Out.ar(0, sig.dup);
}).add;

SynthDef(\upicLive, { |freq = 440, amp = 0.0, gliss = 0.2, dens = 0.8|
    var f  = Lag.kr(freq, 0.03);
    var a  = Lag.kr(amp,  0.03);
    var g  = Lag.kr(gliss,0.03);
    var d  = Lag.kr(dens, 0.03);
    var mod = LFNoise2.kr(d * 10) * g * 100;
    var sig = SinOsc.ar(f + mod, 0, a);
    Out.ar(0, sig.dup);
}).add;
)


(
~upicLive = Synth(\upicLive, [\amp, 0.0]);

OSCdef(\upic, { |msg|
    var t = msg[1], f = msg[2], a = msg[3], g = msg[4], d = msg[5];
    Synth(\upicSynth, [\freq, f, \amp, a, \gliss, g, \dens, d]);
}, '/upic');

OSCdef(\upic_live, { |msg|
    var f = msg[1], a = msg[2], g = msg[3], d = msg[4];
    ~upicLive.set(\freq, f, \amp, a, \gliss, g, \dens, d);
}, '/upic_live');

OSCdef(\upic_live_release, {
    ~upicLive.set(\amp, 0.0);
}, '/upic_live_release');
)