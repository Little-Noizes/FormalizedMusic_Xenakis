(
SynthDef("upicSynth", {
    |freq = 440, amp = 0.5, gliss = 0.2, dens = 0.8|
    var env, mod, sig;
    env = EnvGen.kr(Env.perc(0.01, 0.3), doneAction: 2);
    mod = LFNoise2.kr(dens * 10) * gliss * 100; // DSS-style glissando
    sig = SinOsc.ar(freq + mod, 0, amp) * env;
    Out.ar(0, sig.dup);
}).add;

OSCdef(\upic, { |msg|
    var time = msg[1];
    var freq = msg[2];
    var amp = msg[3];
    var gliss = msg[4];
    var dens = msg[5];
    Synth("upicSynth", [\freq, freq, \amp, amp, \gliss, gliss, \dens, dens]);
}, '/upic');
)
(
// Continuous synth to steer while drawing
SynthDef(\upicLive, { |freq = 440, amp = 0.0, gliss = 0.2, dens = 0.8|
    // Smooth control to avoid clicks on rapid updates
    var f  = Lag.kr(freq, 0.03);
    var a  = Lag.kr(amp,  0.03);
    var g  = Lag.kr(gliss,0.03);
    var d  = Lag.kr(dens, 0.03);

    // Your DSS-style modulation (reuse your LFNoise2 idea)
    var mod = LFNoise2.kr(d * 10) * g * 100;

    // Use your same carrier; duplicate to stereo
    var sig = SinOsc.ar(f + mod, 0, a);
    Out.ar(0, sig.dup);
}).add;

// Create one persistent synth (silent at start)
~upicLive = Synth(\upicLive, [\amp, 0.0]);

// Live OSC: update the running synth while drawing
OSCdef(\upic_live, { |msg|
    // msg = [ '/upic_live', freq, amp, gliss, dens ]
    var freq = msg[1], amp = msg[2], gliss = msg[3], dens = msg[4];
    ~upicLive.set(\freq, freq, \amp, amp, \gliss, gliss, \dens, dens);
}, '/upic_live');

// When mouse is released in the UI, fade out
OSCdef(\upic_live_release, {
    ~upicLive.set(\amp, 0.0);
}, '/upic_live_release');
)
