#python benchmark_receiver.py -a addr=192.168.10.2 --rx-freq=2.45e9 -m gmsk -r 500e3 --to-file='/test.png'
from gnuradio import gr, gru
from gnuradio import blocks
from gnuradio import eng_notation
from gnuradio.blocks.blocks_swig0 import file_sink
from gnuradio.eng_option import eng_option
from optparse import OptionParser
from gnuradio import digital
from gnuradio.filter import firdes

import random,struct,sys,socket

# from current dir (GNURadio->digital->narrowband)
from receive_path import receive_path
from uhd_interface import uhd_receiver

class my_top_block(gr.top_block):

    def __init__(self, demodulator, rx_callback, options):
        gr.top_block.__init__(self)
        if(options.rx_freq is not None):
            args=demodulator.extract_kwargs_from_options(options)
            symbol_rate=options.bitrate/demodulator(**args).bits_per_symbol()
            self.source=uhd_receiver(options.args, symbol_rate,
                                    options.samples_per_symbol,options.rx_freq,
                                    options.lo_offset,options.rx_gain,
                                    options.spec,options.antenna,
                                    options.clock_source,options.verbose)
            options.samples_per_symbol=self.source._sps
        elif(options.to_file is not None):
            sys.stderr.write("saving samples to '%s'.\n\n"%(options.to_file))
            self.sink=blocks.file_sink(gr.sizeof_gr_complex,options.to_file)
        else:
            sys.stderr.write("no sink defined, dumping samples to null sink.\n\n")
            self.sink=blocks.null_sink(gr.sizeof_grcomplex)

        self.rxpath=receive_path(demodulator,rx_callback,options)
        self.connect(self.source,self.rxpath)

# /////////////////////////////////////////////////////////////////////////////
#                                   main
# /////////////////////////////////////////////////////////////////////////////

global n_rcvd, n_right

def main():
    global n_rcvd, n_right,temp_message,error

    temp_message=''
    n_rcvd = 0
    n_right = 0
    error = 0

    BUFF_SIZE = 65536
    
    demods = digital.modulation_utils.type_1_demods()

    # Create Options Parser:
    parser = OptionParser (option_class=eng_option, conflict_handler="resolve")
    expert_grp = parser.add_option_group("Expert")

    parser.add_option("-m", "--modulation", type="choice", choices=demods.keys(), 
                      default='gmsk',
                      help="Select modulation from: %s [default=%%default]"
                            % (', '.join(demods.keys()),))
    parser.add_option("","--to-file",default=None,
                        help="use file for packet contents")
    parser.add_option("","--live",action="store_true",default=False,
                       help="live play or not" )

    receive_path.add_options(parser, expert_grp)
    uhd_receiver.add_options(parser)

    for mod in demods.values():
        mod.add_options(expert_grp)

    (options, args) = parser.parse_args ()

    if options.live:
        server_socket = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
        server_socket.setsockopt(socket.SOL_SOCKET,socket.SO_RCVBUF,BUFF_SIZE)
        HostIP=raw_input('please input server IP address (default is 10.106.67.99): ')
        if HostIP=='':
            HOST='10.106.67.99'
        else:
            HOST=HostIP
        HostPort=raw_input('please input server port (default is 1234):')
        if HostPort=='':
            PORT=1234
        else:
            PORT=int(HostPort)
        socket_address = (HOST,PORT)
        server_socket.bind(socket_address)
        print('Listening at',socket_address)
        msg,client_addr = server_socket.recvfrom(BUFF_SIZE)
        print 'Got connection from', client_addr

    def rx_callback(ok, payload):
        global n_rcvd, n_right,temp_message,error
        (pktno,) = struct.unpack('!H', payload[0:2])
        n_rcvd += 1
        if ok:
            n_right += 1
        else: 
            error += 1
        error_ratio = (n_rcvd-n_right)/n_rcvd
        print "ok = %5s  pktno = %4d  n_rcvd = %4d  n_right = %4d  error = %4d" % (
            ok, pktno, n_rcvd, n_right, error)
        if options.live==False:
            write_to_file(payload[2:])
        else:
            if struct.unpack('!H',payload[2:4])==(78,):
                temp_message = temp_message + payload[4:]
            elif struct.unpack('!H',payload[2:4])==(89,):
                temp_message = temp_message + payload[4:]
                server_socket.sendto(temp_message,client_addr)
                temp_message=''
            else:
                temp_message = payload[2:]
                server_socket.sendto(temp_message,client_addr)
                temp_message=''

    if options.to_file is not None:
        f=open(options.to_file,'w')

    def write_to_file(data):
        if options.to_file is not None:
            f.write(data)

    if len(args) != 0:
        parser.print_help(sys.stderr)
        sys.exit(1)

    if options.rx_freq is None:
        sys.stderr.write("You must specify -f FREQ or --freq FREQ\n")
        parser.print_help(sys.stderr)
        sys.exit(1)
    
    # build the graph
    tb = my_top_block(demods[options.modulation], rx_callback, options)

    r = gr.enable_realtime_scheduling()
    if r != gr.RT_OK:
        print "Warning: Failed to enable realtime scheduling."

    tb.start()        
    tb.wait()         # wait for it to finish

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pass
