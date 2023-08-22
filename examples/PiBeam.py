from machine import Timer, Pin,PWM,SPI
from array import array
from utime import ticks_us
from utime import ticks_us, ticks_diff
from machine import Pin, freq
from sys import platform
import time,utime
import st7789

import rp2

class LCD:
    def __init__(self):
      self.spi = SPI(1, baudrate=40000000, sck=Pin(10), mosi=Pin(11))
      
    def display(self):
          self.tft = st7789.ST7789(self.spi,135,240,reset=Pin(12, Pin.OUT),cs=Pin(9, Pin.OUT),dc=Pin(8, Pin.OUT),backlight=Pin(13, Pin.OUT),rotation=1)
          return self.tft

_CMD_TIMEOUT = const(100)
_R1_IDLE_STATE = const(1 << 0)
_R1_ILLEGAL_COMMAND = const(1 << 2)
_TOKEN_CMD25 = const(0xFC)
_TOKEN_STOP_TRAN = const(0xFD)
_TOKEN_DATA = const(0xFE)

class IR_Receiver:
    def __init__(self):
        self.IR_RX  = self.IR_RX()
        
    class IR_RX():
        # Result/error codes
        # Repeat button code
        REPEAT = -1
        # Error codes
        BADSTART = -2
        BADBLOCK = -3
        BADREP = -4
        OVERRUN = -5
        BADDATA = -6
        BADADDR = -7

        def __init__(self,nedges, tblock, callback, *args):  # Optional args for callback
            self._pin_rx = Pin(1, Pin.IN)
            self._nedges = nedges
            self._tblock = tblock
            self.callback = callback
            self.args = args
            self._errf = lambda _ : None
            self.verbose = False

            self._times = array('i',  (0 for _ in range(nedges + 1)))  # +1 for overrun
            self._pin_rx.irq(handler = self._cb_pin, trigger = (Pin.IRQ_FALLING | Pin.IRQ_RISING))
            self.edge = 0
            self.tim = Timer(-1)  # Sofware timer
            self.cb = self.decode

        # Pin interrupt. Save time of each edge for later decode.
        def _cb_pin(self, line):
            t = ticks_us()
            # On overrun ignore pulses until software timer times out
            if self.edge <= self._nedges:  # Allow 1 extra pulse to record overrun
                if not self.edge:  # First edge received
                    self.tim.init(period=self._tblock , mode=Timer.ONE_SHOT, callback=self.cb)
                self._times[self.edge] = t
                self.edge += 1

        def do_callback(self, cmd, addr, ext, thresh=0):
            self.edge = 0
            if cmd >= thresh:
                self.callback(cmd, addr, ext, *self.args)
            else:
                self._errf(cmd)

        def error_function(self, func):
            self._errf = func

        def close(self):
            self._pin_rx.irq(handler = None)
            self.tim.deinit()

    class IR_GET(IR_RX):
        def __init__(self, pin_rx, nedges=100, twait=100, display=True):
            self.display = display
            super().__init__(pin_rx, nedges, twait, lambda *_ : None)
            self.data = None

        def decode(self, _):
            def near(v, target):
                return target * 0.8 < v < target * 1.2
            lb = self.edge - 1  # Possible length of burst
            if lb < 3:
                return  # Noise
            burst = []
            for x in range(lb):
                dt = ticks_diff(self._times[x + 1], self._times[x])
                if x > 0 and dt > 10000:  # Reached gap between repeats
                    break
                burst.append(dt)
            lb = len(burst)  # Actual length
            # Duration of pulse train 24892 for RC-5 22205 for RC-6
            duration = ticks_diff(self._times[lb - 1], self._times[0])

            if self.display:
                for x, e in enumerate(burst):
                    print('{:03d} {:5d}'.format(x, e))
                print()
                # Attempt to determine protocol
                ok = False  # Protocol not yet found
                if near(burst[0], 9000) and lb == 67:
                    print('NEC')
                    ok = True

                if not ok and near(burst[0], 2400) and near(burst[1], 600):  # Maybe Sony
                    try:
                        nbits = {25:12, 31:15, 41:20}[lb]
                    except KeyError:
                        pass
                    else:
                        ok = True
                        print('Sony {}bit'.format(nbits))

                if not ok and near(burst[0], 889):  # Maybe RC-5
                    if near(duration, 24892) and near(max(burst), 1778):
                        print('Philps RC-5')
                        ok = True

                if not ok and near(burst[0], 2666) and near(burst[1], 889):  # RC-6?
                    if near(duration, 22205) and near(burst[1], 889) and near(burst[2], 444):
                        print('Philips RC-6 mode 0')
                        ok = True

                if not ok and near(burst[0], 2000) and near(burst[1], 1000):
                    if near(duration, 19000):
                        print('Microsoft MCE edition protocol.')
                        # Constant duration, variable burst length, presumably bi-phase
                        print('Protocol start {} {} Burst length {} duration {}'.format(burst[0], burst[1], lb, duration))
                        ok = True

                if not ok and near(burst[0], 4500) and near(burst[1], 4500) and lb == 67:  # Samsung
                    print('Samsung')
                    ok = True

                if not ok and near(burst[0], 3500) and near(burst[1], 1680):  # Panasonic?
                    print('Unsupported protocol. Panasonic?')
                    ok = True

                if not ok:
                    print('Unknown protocol start {} {} Burst length {} duration {}'.format(burst[0], burst[1], lb, duration))

                print()
            self.data = burst
            # Set up for new data burst. Run null callback
            self.do_callback(0, 0, 0)

        def acquire(self):
            while self.data is None:
                sleep_ms(5)
            self.close()
            return self.data
        
    ######################## MEC ######################################   
    class MCE(IR_RX):
        init_cs = 4  
        def __init__(self,callback, *args):
            # Block lasts ~19ms and has <= 34 edges
            super().__init__(34, 25, callback, *args)

        def decode(self, _):
            def check(v):
                if self.init_cs == -1:
                    return True
                csum = v >> 12
                cs = self.init_cs
                for _ in range(12):
                    if v & 1:
                        cs += 1
                    v >>= 1
                return cs == csum

            try:
                t0 = ticks_diff(self._times[1], self._times[0])  # 2000μs mark
                t1 = ticks_diff(self._times[2], self._times[1])  # 1000μs space
                if not ((1800 < t0 < 2200) and (800 < t1 < 1200)):
                    raise RuntimeError(self.BADSTART)
                nedges = self.edge  # No. of edges detected
                if not 14 <= nedges <= 34:
                    raise RuntimeError(self.OVERRUN if nedges > 28 else self.BADSTART)
                # Manchester decode
                mask = 1
                bit = 1
                v = 0
                x = 2
                for _ in range(16):
                    # -1 convert count to index, -1 because we look ahead
                    if x > nedges - 2:
                        raise RuntimeError(self.BADBLOCK)
                    # width is 500/1000 nominal
                    width = ticks_diff(self._times[x + 1], self._times[x])
                    if not 250 < width < 1350:
                        self.verbose and print('Bad block 3 Width', width, 'x', x)
                        raise RuntimeError(self.BADBLOCK)
                    short = int(width < 750)
                    bit ^= short ^ 1
                    v |= mask if bit else 0
                    mask <<= 1
                    x += 1 + short

                self.verbose and print(bin(v))
                if not check(v):
                    raise RuntimeError(self.BADDATA)
                val = (v >> 6) & 0x3f
                addr = v & 0xf  # Constant for all buttons on my remote
                ctrl = (v >> 4) & 3

            except RuntimeError as e:
                val, addr, ctrl = e.args[0], 0, 0
            # Set up for new data burst and run user callback/error function
            self.do_callback(val, addr, ctrl)
            
    ######################## NEC ######################################
    class NEC(IR_RX):
        def __init__(self, extended, samsung, callback, *args):
            # Block lasts <= 80ms (extended mode) and has 68 edges
            super().__init__(68, 80, callback, *args)
            self._extended = extended
            self._addr = 0
            self._leader = 2500 if samsung else 4000  # 4.5ms for Samsung else 9ms

        def decode(self, _):
            try:
                if self.edge > 68:
                    raise RuntimeError(self.OVERRUN)
                width = ticks_diff(self._times[1], self._times[0])
                if width < self._leader:  # 9ms leading mark for all valid data
                    raise RuntimeError(self.BADSTART)
                width = ticks_diff(self._times[2], self._times[1])
                if width > 3000:  # 4.5ms space for normal data
                    if self.edge < 68:  # Haven't received the correct number of edges
                        raise RuntimeError(self.BADBLOCK)
                    # Time spaces only (marks are always 562.5µs)
                    # Space is 1.6875ms (1) or 562.5µs (0)
                    # Skip last bit which is always 1
                    val = 0
                    for edge in range(3, 68 - 2, 2):
                        val >>= 1
                        if ticks_diff(self._times[edge + 1], self._times[edge]) > 1120:
                            val |= 0x80000000
                elif width > 1700: # 2.5ms space for a repeat code. Should have exactly 4 edges.
                    raise RuntimeError(self.REPEAT if self.edge == 4 else self.BADREP)  # Treat REPEAT as error.
                else:
                    raise RuntimeError(self.BADSTART)
                addr = val & 0xff  # 8 bit addr
                cmd = (val >> 16) & 0xff
                if cmd != (val >> 24) ^ 0xff:
                    raise RuntimeError(self.BADDATA)
                if addr != ((val >> 8) ^ 0xff) & 0xff:  # 8 bit addr doesn't match check
                    if not self._extended:
                        raise RuntimeError(self.BADADDR)
                    addr |= val & 0xff00  # pass assumed 16 bit address to callback
                self._addr = addr
            except RuntimeError as e:
                cmd = e.args[0]
                addr = self._addr if cmd == self.REPEAT else 0  # REPEAT uses last address
            # Set up for new data burst and run user callback
            self.do_callback(cmd, addr, 0, self.REPEAT)

    class NEC_8(NEC):
        def __init__(self,callback, *args):
            super().__init__(False, False, callback, *args)

    class NEC_16(NEC):
        def __init__(self, callback, *args):
            super().__init__(True, False, callback, *args)

    class SAMSUNG(NEC):
        def __init__(self,callback, *args):
            super().__init__(True, True, callback, *args)
    
    
    ######################### PHILIPS RC ########################3
    class RC5_IR(IR_RX):
        def __init__(self,callback, *args):
            # Block lasts <= 30ms and has <= 28 edges
            super().__init__(28, 30, callback, *args)

        def decode(self, _):
            try:
                nedges = self.edge  # No. of edges detected
                if not 14 <= nedges <= 28:
                    raise RuntimeError(self.OVERRUN if nedges > 28 else self.BADSTART)
                # Regenerate bitstream
                bits = 1
                bit = 1
                v = 1  # 14 bit bitstream, MSB always 1
                x = 0
                while bits < 14:
                    # -1 convert count to index, -1 because we look ahead
                    if x > nedges - 2:
                        print('Bad block 1 edges', nedges, 'x', x)
                        raise RuntimeError(self.BADBLOCK)
                    # width is 889/1778 nominal
                    width = ticks_diff(self._times[x + 1], self._times[x])
                    if not 500 < width < 2100:
                        self.verbose and print('Bad block 3 Width', width, 'x', x)
                        raise RuntimeError(self.BADBLOCK)
                    short = width < 1334
                    if not short:
                        bit ^= 1
                    v <<= 1
                    v |= bit
                    bits += 1
                    x += 1 + int(short)
                self.verbose and print(bin(v))
                # Split into fields (val, addr, ctrl)
                val = (v & 0x3f) | (0 if ((v >> 12) & 1) else 0x40)  # Correct the polarity of S2
                addr = (v >> 6) & 0x1f
                ctrl = (v >> 11) & 1

            except RuntimeError as e:
                val, addr, ctrl = e.args[0], 0, 0
            # Set up for new data burst and run user callback
            self.do_callback(val, addr, ctrl)


    class RC6_M0(IR_RX):
        # Even on Pyboard D the 444μs nominal pulses can be recorded as up to 705μs
        # Scope shows 360-520 μs (-84μs +76μs relative to nominal)
        # Header nominal 2666, 889, 444, 889, 444, 444, 444, 444 carrier ON at end
        hdr = ((1800, 4000), (593, 1333), (222, 750), (593, 1333), (222, 750), (222, 750), (222, 750), (222, 750))
        def __init__(self,callback, *args):
            # Block lasts 23ms nominal and has <=44 edges
            super().__init__(44, 30, callback, *args)

        def decode(self, _):
            try:
                nedges = self.edge  # No. of edges detected
                if not 22 <= nedges <= 44:
                    raise RuntimeError(self.OVERRUN if nedges > 28 else self.BADSTART)
                for x, lims in enumerate(self.hdr):
                    width = ticks_diff(self._times[x + 1], self._times[x])
                    if not (lims[0] < width < lims[1]):
                        self.verbose and print('Bad start', x, width, lims)
                        raise RuntimeError(self.BADSTART)
                x += 1
                width = ticks_diff(self._times[x + 1], self._times[x])
                # 2nd bit of last 0 is 444μs (0) or 1333μs (1)
                if not 222 < width < 1555:
                    self.verbose and print('Bad block 1 Width', width, 'x', x)
                    raise RuntimeError(self.BADBLOCK)
                short = width < 889
                v = int(not short)
                bit = v
                bits = 1  # Bits decoded
                x += 1 + int(short)
                width = ticks_diff(self._times[x + 1], self._times[x])
                if not 222 < width < 1555:
                    self.verbose and print('Bad block 2 Width', width, 'x', x)
                    raise RuntimeError(self.BADBLOCK)
                short = width < 1111
                if not short:
                    bit ^= 1
                x += 1 + int(short)  # If it's short, we know width of next
                v <<= 1
                v |= bit  # MSB of result
                bits += 1
                # Decode bitstream
                while bits < 17:
                    # -1 convert count to index, -1 because we look ahead
                    if x > nedges - 2:
                        raise RuntimeError(self.BADBLOCK)
                    # width is 444/889 nominal
                    width = ticks_diff(self._times[x + 1], self._times[x])
                    if not 222 < width < 1111:
                        self.verbose and print('Bad block 3 Width', width, 'x', x)
                        raise RuntimeError(self.BADBLOCK)
                    short = width < 666
                    if not short:
                        bit ^= 1
                    v <<= 1
                    v |= bit
                    bits += 1
                    x += 1 + int(short)

                if self.verbose:
                     ss = '20-bit format {:020b} x={} nedges={} bits={}'
                     print(ss.format(v, x, nedges, bits))

                val = v & 0xff
                addr = (v >> 8) & 0xff
                ctrl = (v >> 16) & 1
            except RuntimeError as e:
                val, addr, ctrl = e.args[0], 0, 0
            # Set up for new data burst and run user callback
            self.do_callback(val, addr, ctrl)
    ####################################################################
            
    ######################## SONY ######################################
    class SONY(IR_RX):  # Abstract base class
        def __init__(self,bits, callback, *args):
            # 20 bit block has 42 edges and lasts <= 39ms nominal. Add 4ms to time
            # for tolerances except in 20 bit case where timing is tight with a
            # repeat period of 45ms.
            t = int(3 + bits * 1.8) + (1 if bits == 20 else 4)
            super().__init__(2 + bits * 2, t, callback, *args)
            self._addr = 0
            self._bits = 20

        def decode(self, _):
            try:
                nedges = self.edge  # No. of edges detected
                self.verbose and print('nedges', nedges)
                if nedges > 42:
                    raise RuntimeError(self.OVERRUN)
                bits = (nedges - 2) // 2
                if nedges not in (26, 32, 42) or bits > self._bits:
                    raise RuntimeError(self.BADBLOCK)
                self.verbose and print('SIRC {}bit'.format(bits))
                width = ticks_diff(self._times[1], self._times[0])
                if not 1800 < width < 3000:  # 2.4ms leading mark for all valid data
                    raise RuntimeError(self.BADSTART)
                width = ticks_diff(self._times[2], self._times[1])
                if not 350 < width < 1000:  # 600μs space
                    raise RuntimeError(self.BADSTART)

                val = 0  # Data received, LSB 1st
                x = 2
                bit = 1
                while x <= nedges - 2:
                    if ticks_diff(self._times[x + 1], self._times[x]) > 900:
                        val |= bit
                    bit <<= 1
                    x += 2
                cmd = val & 0x7f  # 7 bit command
                val >>= 7
                if nedges < 42:
                    addr = val & 0xff  # 5 or 8 bit addr
                    val = 0
                else:
                    addr = val & 0x1f  # 5 bit addr
                    val >>= 5  # 8 bit extended
            except RuntimeError as e:
                cmd = e.args[0]
                addr = 0
                val = 0
            self.do_callback(cmd, addr, val)

    class SONY_12(SONY):
        def __init__(self,callback, *args):
            super().__init__(12, callback, *args)

    class SONY_15(SONY):
        def __init__(self,callback, *args):
            super().__init__(15, callback, *args)

    class SONY_20(SONY):
        def __init__(self,callback, *args):
            super().__init__(20, callback, *args)



@rp2.asm_pio(set_init=rp2.PIO.OUT_LOW, autopull=True, pull_thresh=32)
def pulsetrain():
        wrap_target()
        out(x, 32)  # No of 1MHz ticks. Block if FIFO MT at end.
        irq(rel(0))
        set(pins, 1)  # Set pin high
        label('loop')
        jmp(x_dec,'loop')
        irq(rel(0))
        set(pins, 0)  # Set pin low
        out(y, 32)  # Low time.
        label('loop_lo')
        jmp(y_dec,'loop_lo')
        wrap()

@rp2.asm_pio(autopull=True, pull_thresh=32)
def irqtrain():
        wrap_target()
        out(x, 32)  # No of 1MHz ticks. Block if FIFO MT at end.
        irq(rel(0))
        label('loop')
        jmp(x_dec,'loop')
        wrap()

class DummyPWM:
        def duty_u16(self, _):
            pass

class RP2_RMT:

        def __init__(self, pin_pulse=None, carrier=None, sm_no=0, sm_freq=1_000_000):
            if carrier is None:
                self.pwm = DummyPWM()
                self.duty = (0, 0)
            else:
                pin_car, freq, duty = carrier
                self.pwm = PWM(pin_car)  # Set up PWM with carrier off.
                self.pwm.freq(freq)
                self.pwm.duty_u16(0)
                self.duty = (int(0xffff * duty // 100), 0)
            if pin_pulse is None:
                self.sm = rp2.StateMachine(sm_no, irqtrain, freq=sm_freq)
            else:
                self.sm = rp2.StateMachine(sm_no, pulsetrain, freq=sm_freq, set_base=pin_pulse)
            self.apt = 0  # Array index
            self.arr = None  # Array
            self.ict = None  # Current IRQ count
            self.icm = 0  # End IRQ count
            self.reps = 0  # 0 == forever n == no. of reps
            rp2.PIO(0).irq(self._cb)

        # IRQ callback. Because of FIFO IRQ's keep arriving after STOP.
        def _cb(self, pio):
            self.pwm.duty_u16(self.duty[self.ict & 1])
            self.ict += 1
            if d := self.arr[self.apt]:  # If data available feed FIFO
                self.sm.put(d)
                self.apt += 1
            else:
                if r := self.reps != 1:  # All done if reps == 1
                    if r:  # 0 == run forever
                        self.reps -= 1
                    self.sm.put(self.arr[0])
                    self.apt = 1  # Set pointer and count to state
                    self.ict = 1  # after 1st IRQ

        # Arg is an array of times in μs terminated by 0. 
        def send(self, ar, reps=1, check=True):
            self.sm.active(0)
            self.reps = reps
            ar[-1] = 0  # Ensure at least one STOP
            for x, d in enumerate(ar):  # Find 1st STOP
                if d == 0:
                    break
            if check:
                # Pulse train must end with a space otherwise we leave carrier on.
                # So, if it ends with a mark, append a space. Note __init__.py
                # ensures that there is room in array.
                if (x & 1):
                    ar[x] = 1  # space. Duration doesn't matter.
                    x += 1
                    ar[x] = 0  # STOP
            self.icm = x  # index of 1st STOP
            mv = memoryview(ar)
            n = min(x, 4)  # Fill FIFO if there are enough data points.
            self.sm.put(mv[0 : n])
            self.arr = ar  # Initial conditions for ISR
            self.apt = n  # Point to next data value
            self.ict = 0  # IRQ count
            self.sm.active(1)

        def busy(self):
            if self.ict is None:
                return False  # Just instantiated
            return self.ict < self.icm

        def cancel(self):
            self.reps = 1


class IR_Transmitter:
    # Shared by NEC
    STOP = const(0)  # End of data

    # IR abstract base class. Array holds periods in μs between toggling 36/38KHz
    # carrier on or off. Physical transmission occurs in an ISR context controlled
    # by timer 2 and timer 5. See TRANSMITTER.md for details of operation.
    def __init__(self):
        ## instantiating the 'Inner' class
        self.IR = self.IR()
        
    class IR_TX:
        _active_high = True  # Hardware turns IRLED on if pin goes high.
        _space = 0  # Duty ratio that causes IRLED to be off
        timeit = False  # Print timing info

        @classmethod
        def active_low(cls):
            if ESP32:
                raise ValueError('Cannot set active low on ESP32')
            cls._active_high = False
            cls._space = 100

        def __init__(self,cfreq, asize, duty, verbose):
            self.pin_tx = Pin(0,Pin.OUT, value = 1)
            self._rmt = RP2_RMT(pin_pulse=None, carrier=(self.pin_tx, cfreq, duty))  # 1μs resolution
            asize += 1  # Allow for possible extra space pulse

            self._tcb = self._cb  # Pre-allocate
            self._arr = array('H', 0 for _ in range(asize))  # on/off times (μs)
            self._mva = memoryview(self._arr)
            # Subclass interface
            self.verbose = verbose
            self.carrier = False  # Notional carrier state while encoding biphase
            self.aptr = 0  # Index into array

        def _cb(self, t):  # T5 callback, generate a carrier mark or space
            t.deinit()
            p = self.aptr
            v = self._arr[p]
            if v == STOP:
                self._ch.pulse_width_percent(self._space)  # Turn off IR LED.
                return
            self._ch.pulse_width_percent(self._space if p & 1 else self._duty)
            self._tim.init(prescaler=84, period=v, callback=self._tcb)
            self.aptr += 1

        # Public interface
        # Before populating array, zero pointer, set notional carrier state (off).
        def transmit(self, addr, data, toggle=0, validate=False):  # NEC: toggle is unused
            t = ticks_us()
            if validate:
                if addr > self.valid[0] or addr < 0:
                    raise ValueError('Address out of range', addr)
                if data > self.valid[1] or data < 0:
                    raise ValueError('Data out of range', data)
                if toggle > self.valid[2] or toggle < 0:
                    raise ValueError('Toggle out of range', toggle)
            self.aptr = 0  # Inital conditions for tx: index into array
            self.carrier = False
            self.tx(addr, data, toggle)  # Subclass populates ._arr
            self.trigger()  # Initiate transmission
            if self.timeit:
                dt = ticks_diff(ticks_us(), t)
                print('Time = {}μs'.format(dt))

        # Subclass interface
        def trigger(self):  # Used by NEC to initiate a repeat frame
            self.append(STOP)
            self._rmt.send(self._arr)
 

        def append(self, *times):  # Append one or more time peiods to ._arr
            for t in times:
                self._arr[self.aptr] = t
                self.aptr += 1
                self.carrier = not self.carrier  # Keep track of carrier state
                self.verbose and print('append', t, 'carrier', self.carrier)

        def add(self, t):  # Increase last time value (for biphase)
            assert t > 0
            self.verbose and print('add', t)
            # .carrier unaffected
            self._arr[self.aptr - 1] += t


    # Given an iterable (e.g. list or tuple) of times, emit it as an IR stream.
    class Player(IR_TX):

        def __init__(self,freq=38000, verbose=False):  # NEC specifies 38KHz
            super().__init__(freq, 68, 33, verbose)  # Measured duty ratio 33%

        def play(self, lst):
            for x, t in enumerate(lst):
                self._arr[x] = t
            self.aptr = x + 1
            self.trigger()

    _TBIT = const(500)  # Time (μs) for pulse of carrier


    class MCE(IR_TX):
        valid = (0xf, 0x3f, 3)  # Max addr, data, toggle
        init_cs = 4  # http://www.hifi-remote.com/johnsfine/DecodeIR.html#OrtekMCE says 3

        def __init__(self,freq=38000, verbose=False):
            super().__init__(freq, 34, 30, verbose)

        def tx(self, addr, data, toggle):
            def checksum(v):
                cs = self.init_cs
                for _ in range(12):
                    if v & 1:
                        cs += 1
                    v >>= 1
                return cs

            self.append(2000, 1000, _TBIT)
            d = ((data & 0x3f) << 6) | (addr & 0xf)  | ((toggle & 3) << 4)
            d |= checksum(d) << 12
            self.verbose and print(bin(d))

            mask = 1
            while mask < 0x10000:
                bit = bool(d & mask)
                if bit ^ self.carrier:
                    self.add(_TBIT)
                    self.append(_TBIT)
                else:
                    self.append(_TBIT, _TBIT)
                mask <<= 1

    _TBURST = const(563)
    _T_ONE = const(1687)

    class NEC(IR_TX):
        valid = (0xffff, 0xff, 0)  # Max addr, data, toggle
        samsung = False

        def __init__(self,freq=38000, verbose=False):  # NEC specifies 38KHz also Samsung
            super().__init__(freq, 68, 33, verbose)  # Measured duty ratio 33%

        def _bit(self, b):
            self.append(_TBURST, _T_ONE if b else _TBURST)

        def tx(self, addr, data, _):  # Ignore toggle
            if self.samsung:
                self.append(4500, 4500)
            else:
                self.append(9000, 4500)
            if addr < 256:  # Short address: append complement
                if self.samsung:
                  addr |= addr << 8
                else:
                  addr |= ((addr ^ 0xff) << 8)
            for _ in range(16):
                self._bit(addr & 1)
                addr >>= 1
            data |= ((data ^ 0xff) << 8)
            for _ in range(16):
                self._bit(data & 1)
                data >>= 1
            self.append(_TBURST)

        def repeat(self):
            self.aptr = 0
            self.append(9000, 2250, _TBURST)
            self.trigger()  # Initiate physical transmission.

    # Philips RC5 protocol
    _T_RC5 = const(889)  # Time for pulse of carrier


    class RC5(IR_TX):
        valid = (0x1f, 0x7f, 1)  # Max addr, data, toggle

        def __init__(self,freq=36000, verbose=False):
            super().__init__( freq, 28, 30, verbose)

        def tx(self, addr, data, toggle):  # Fix RC5X S2 bit polarity
            d = (data & 0x3f) | ((addr & 0x1f) << 6) | (((data & 0x40) ^ 0x40) << 6) | ((toggle & 1) << 11)
            self.verbose and print(bin(d))
            mask = 0x2000
            while mask:
                if mask == 0x2000:
                    self.append(_T_RC5)
                else:
                    bit = bool(d & mask)
                    if bit ^ self.carrier:
                        self.add(_T_RC5)
                        self.append(_T_RC5)
                    else:
                        self.append(_T_RC5, _T_RC5)
                mask >>= 1

    # Philips RC6 mode 0 protocol
    _T_RC6 = const(444)
    _T2_RC6 = const(889)

    class RC6_M0(IR_TX):
        valid = (0xff, 0xff, 1)  # Max addr, data, toggle

        def __init__(self,freq=36000, verbose=False):
            super().__init__(freq, 44, 30, verbose)

        def tx(self, addr, data, toggle):
            # leader, 1, 0, 0, 0
            self.append(2666, _T2_RC6, _T_RC6, _T2_RC6, _T_RC6, _T_RC6, _T_RC6, _T_RC6, _T_RC6)
            # Append a single bit of twice duration
            if toggle:
                self.add(_T2_RC6)
                self.append(_T2_RC6)
            else:
                self.append(_T2_RC6, _T2_RC6)
            d = (data & 0xff) | ((addr & 0xff) << 8)
            mask = 0x8000
            self.verbose and print('toggle', toggle, self.carrier, bool(d & mask))
            while mask:
                bit = bool(d & mask)
                if bit ^ self.carrier:
                    self.append(_T_RC6, _T_RC6)
                else:
                    self.add(_T_RC6)
                    self.append(_T_RC6)
                mask >>= 1

    class SONY_1(IR_TX):

        def __init__(self,bits, freq, verbose):
            super().__init__(freq, 3 + bits * 2, 30, verbose)
            if bits not in (12, 15, 20):
                raise ValueError('bits must be 12, 15 or 20.')
            self.bits = bits

        def tx(self, addr, data, ext):
            self.append(2400, 600)
            bits = self.bits
            v = data & 0x7f
            if bits == 12:
                v |= (addr & 0x1f) << 7
            elif bits == 15:
                v |= (addr & 0xff) << 7
            else:
                v |= (addr & 0x1f) << 7
                v |= (ext & 0xff) << 12
            for _ in range(bits):
                self.append(1200 if v & 1 else 600, 600)
                v >>= 1

    # Sony specifies 40KHz
    class SONY_12(SONY_1):
        valid = (0x1f, 0x7f, 0)  # Max addr, data, toggle
        def __init__(self,freq=40000, verbose=False):
            super().__init__( 12, freq, verbose)

    class SONY_15(SONY_1):
        valid = (0xff, 0x7f, 0)  # Max addr, data, toggle
        def __init__(self,freq=40000, verbose=False):
            super().__init__(15, freq, verbose)

    class SONY_20(SONY_1):
        valid = (0x1f, 0x7f, 0xff)  # Max addr, data, toggle
        def __init__(self,freq=40000, verbose=False):
            super().__init__(0, freq, verbose)


class BUTTON():
    def __init__(self, button_pin_number):
        """Initialize BUTTON.
        Args:
            button_pin_number (int):  1, 2, 3 for onboard Buttons,
                                      and pass GPIOs number for interfacing external buttons 
        """
        if button_pin_number == 1:
            self.button_pin = Pin(7, Pin.IN, Pin.PULL_UP) #input mode setup for read operation 
        elif button_pin_number == 2:
            self.button_pin = Pin(28, Pin.IN, Pin.PULL_UP)
        elif button_pin_number == 3:
            self.button_pin = Pin(20, Pin.IN,Pin.PULL_UP)
        else :
            self.button_pin = Pin(button_pin_number, Pin.IN) 
            
    def read(self):
        """ provides button status value -> 0 or 1
        """
        return self.button_pin.value()

class LED:
    def __init__(self):
            self.led_pin = Pin(25, Pin.OUT)

    def on(self):
        self.led_pin.value(1)
    
    def off(self):
        self.led_pin.value(0)


class SDCard:
    def __init__(self):
        spi=SPI(0,sck=Pin(18),mosi=Pin(19),miso=Pin(16))
        cs = Pin(17)
        self.spi = spi
        self.cs = cs

        self.cmdbuf = bytearray(6)
        self.dummybuf = bytearray(512)
        self.tokenbuf = bytearray(1)
        for i in range(512):
            self.dummybuf[i] = 0xFF
        self.dummybuf_memoryview = memoryview(self.dummybuf)
        # initialise the card
        self.init_card()

    def init_spi(self, baudrate):
        try:
            master = self.spi.MASTER
        except AttributeError:
            # on ESP8266
            self.spi.init(baudrate=baudrate, phase=0, polarity=0)
        else:
            # on pyboard
            self.spi.init(master, baudrate=baudrate, phase=0, polarity=0)

    def init_card(self):
        # init CS pin
        self.cs.init(self.cs.OUT, value=1)

        # init SPI bus; use low data rate for initialisation
        self.init_spi(100000)

        # clock card at least 100 cycles with cs high
        for i in range(16):
            self.spi.write(b"\xff")

        # CMD0: init card; should return _R1_IDLE_STATE (allow 5 attempts)
        for _ in range(5):
            if self.cmd(0, 0, 0x95) == _R1_IDLE_STATE:
                break
        else:
            raise OSError("no SD card")

        # CMD8: determine card version
        r = self.cmd(8, 0x01AA, 0x87, 4)
        if r == _R1_IDLE_STATE:
            self.init_card_v2()
        elif r == (_R1_IDLE_STATE | _R1_ILLEGAL_COMMAND):
            self.init_card_v1()
        else:
            raise OSError("couldn't determine SD card version")

        # get the number of sectors
        # CMD9: response R2 (R1 byte + 16-byte block read)
        if self.cmd(9, 0, 0, 0, False) != 0:
            raise OSError("no response from SD card")
        csd = bytearray(16)
        self.readinto(csd)
        if csd[0] & 0xC0 == 0x40:  # CSD version 2.0
            self.sectors = ((csd[8] << 8 | csd[9]) + 1) * 1024
        elif csd[0] & 0xC0 == 0x00:  # CSD version 1.0 (old, <=2GB)
            c_size = csd[6] & 0b11 | csd[7] << 2 | (csd[8] & 0b11000000) << 4
            c_size_mult = ((csd[9] & 0b11) << 1) | csd[10] >> 7
            self.sectors = (c_size + 1) * (2 ** (c_size_mult + 2))
        else:
            raise OSError("SD card CSD format not supported")
        # print('sectors', self.sectors)

        # CMD16: set block length to 512 bytes
        if self.cmd(16, 512, 0) != 0:
            raise OSError("can't set 512 block size")

        # set to high data rate now that it's initialised
        self.init_spi(1320000)

    def init_card_v1(self):
        for i in range(_CMD_TIMEOUT):
            self.cmd(55, 0, 0)
            if self.cmd(41, 0, 0) == 0:
                self.cdv = 512
                # print("[SDCard] v1 card")
                return
        raise OSError("timeout waiting for v1 card")

    def init_card_v2(self):
        for i in range(_CMD_TIMEOUT):
            time.sleep_ms(50)
            self.cmd(58, 0, 0, 4)
            self.cmd(55, 0, 0)
            if self.cmd(41, 0x40000000, 0) == 0:
                self.cmd(58, 0, 0, 4)
                self.cdv = 1
                # print("[SDCard] v2 card")
                return
        raise OSError("timeout waiting for v2 card")

    def cmd(self, cmd, arg, crc, final=0, release=True, skip1=False):
        self.cs(0)

        # create and send the command
        buf = self.cmdbuf
        buf[0] = 0x40 | cmd
        buf[1] = arg >> 24
        buf[2] = arg >> 16
        buf[3] = arg >> 8
        buf[4] = arg
        buf[5] = crc
        self.spi.write(buf)

        if skip1:
            self.spi.readinto(self.tokenbuf, 0xFF)

        # wait for the response (response[7] == 0)
        for i in range(_CMD_TIMEOUT):
            self.spi.readinto(self.tokenbuf, 0xFF)
            response = self.tokenbuf[0]
            if not (response & 0x80):
                # this could be a big-endian integer that we are getting here
                for j in range(final):
                    self.spi.write(b"\xff")
                if release:
                    self.cs(1)
                    self.spi.write(b"\xff")
                return response

        # timeout
        self.cs(1)
        self.spi.write(b"\xff")
        return -1

    def readinto(self, buf):
        self.cs(0)

        # read until start byte (0xff)
        for i in range(_CMD_TIMEOUT):
            self.spi.readinto(self.tokenbuf, 0xFF)
            if self.tokenbuf[0] == _TOKEN_DATA:
                break
            time.sleep_ms(1)
        else:
            self.cs(1)
            raise OSError("timeout waiting for response")

        # read data
        mv = self.dummybuf_memoryview
        if len(buf) != len(mv):
            mv = mv[: len(buf)]
        self.spi.write_readinto(mv, buf)

        # read checksum
        self.spi.write(b"\xff")
        self.spi.write(b"\xff")

        self.cs(1)
        self.spi.write(b"\xff")

    def write(self, token, buf):
        self.cs(0)

        # send: start of block, data, checksum
        self.spi.read(1, token)
        self.spi.write(buf)
        self.spi.write(b"\xff")
        self.spi.write(b"\xff")

        # check the response
        if (self.spi.read(1, 0xFF)[0] & 0x1F) != 0x05:
            self.cs(1)
            self.spi.write(b"\xff")
            return

        # wait for write to finish
        while self.spi.read(1, 0xFF)[0] == 0:
            pass

        self.cs(1)
        self.spi.write(b"\xff")

    def write_token(self, token):
        self.cs(0)
        self.spi.read(1, token)
        self.spi.write(b"\xff")
        # wait for write to finish
        while self.spi.read(1, 0xFF)[0] == 0x00:
            pass

        self.cs(1)
        self.spi.write(b"\xff")

    def readblocks(self, block_num, buf):
        nblocks = len(buf) // 512
        assert nblocks and not len(buf) % 512, "Buffer length is invalid"
        if nblocks == 1:
            # CMD17: set read address for single block
            if self.cmd(17, block_num * self.cdv, 0, release=False) != 0:
                # release the card
                self.cs(1)
                raise OSError(5)  # EIO
            # receive the data and release card
            self.readinto(buf)
        else:
            # CMD18: set read address for multiple blocks
            if self.cmd(18, block_num * self.cdv, 0, release=False) != 0:
                # release the card
                self.cs(1)
                raise OSError(5)  # EIO
            offset = 0
            mv = memoryview(buf)
            while nblocks:
                # receive the data and release card
                self.readinto(mv[offset : offset + 512])
                offset += 512
                nblocks -= 1
            if self.cmd(12, 0, 0xFF, skip1=True):
                raise OSError(5)  # EIO

    def writeblocks(self, block_num, buf):
        nblocks, err = divmod(len(buf), 512)
        assert nblocks and not err, "Buffer length is invalid"
        if nblocks == 1:
            # CMD24: set write address for single block
            if self.cmd(24, block_num * self.cdv, 0) != 0:
                raise OSError(5)  # EIO

            # send the data
            self.write(_TOKEN_DATA, buf)
        else:
            # CMD25: set write address for first block
            if self.cmd(25, block_num * self.cdv, 0) != 0:
                raise OSError(5)  # EIO
            # send the data
            offset = 0
            mv = memoryview(buf)
            while nblocks:
                self.write(_TOKEN_CMD25, mv[offset : offset + 512])
                offset += 512
                nblocks -= 1
            self.write_token(_TOKEN_STOP_TRAN)

    def ioctl(self, op, arg):
        if op == 4:  # get number of blocks
            return self.sectors
        