#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#
# SPDX-License-Identifier: GPL-3.0
#
# GNU Radio Python Flow Graph
# Title: OPS-SAT UHF demodulator/decoder
# Author: Fischer Benjamin, Mladenov Tom
# Description: UHF demodulator and decoder application for the ESA OPS-SAT mission
# GNU Radio version: 3.10.9.2

from PyQt5 import Qt
from gnuradio import qtgui
from gnuradio import blocks
from gnuradio import blocks, gr
from gnuradio import digital
from gnuradio import gr
from gnuradio.filter import firdes
from gnuradio.fft import window
import sys
import signal
from PyQt5 import Qt
from argparse import ArgumentParser
from gnuradio.eng_arg import eng_float, intx
from gnuradio import eng_notation
from gnuradio import gr, pdu
from gnuradio import zeromq
import satellites
import satellites.components.demodulators
import sip



class os_demod_decode(gr.top_block, Qt.QWidget):

    def __init__(self):
        gr.top_block.__init__(self, "OPS-SAT UHF demodulator/decoder", catch_exceptions=True)
        Qt.QWidget.__init__(self)
        self.setWindowTitle("OPS-SAT UHF demodulator/decoder")
        qtgui.util.check_set_qss()
        try:
            self.setWindowIcon(Qt.QIcon.fromTheme('gnuradio-grc'))
        except BaseException as exc:
            print(f"Qt GUI: Could not set Icon: {str(exc)}", file=sys.stderr)
        self.top_scroll_layout = Qt.QVBoxLayout()
        self.setLayout(self.top_scroll_layout)
        self.top_scroll = Qt.QScrollArea()
        self.top_scroll.setFrameStyle(Qt.QFrame.NoFrame)
        self.top_scroll_layout.addWidget(self.top_scroll)
        self.top_scroll.setWidgetResizable(True)
        self.top_widget = Qt.QWidget()
        self.top_scroll.setWidget(self.top_widget)
        self.top_layout = Qt.QVBoxLayout(self.top_widget)
        self.top_grid_layout = Qt.QGridLayout()
        self.top_layout.addLayout(self.top_grid_layout)

        self.settings = Qt.QSettings("GNU Radio", "os_demod_decode")

        try:
            geometry = self.settings.value("geometry")
            if geometry:
                self.restoreGeometry(geometry)
        except BaseException as exc:
            print(f"Qt GUI: Could not restore geometry: {str(exc)}", file=sys.stderr)

        ##################################################
        # Variables
        ##################################################
        self.samp_rate = samp_rate = 57600
        self.baud_rate = baud_rate = 9600
        self.gaussian_taps = gaussian_taps = firdes.gaussian (1.5, 2* (samp_rate / baud_rate) , 0.5, 12)
        self.gain_mu = gain_mu = 0.175

        ##################################################
        # Blocks
        ##################################################

        self.zeromq_sub_source_0 = zeromq.sub_source(gr.sizeof_gr_complex, 1, 'tcp://127.0.0.1:5555', 100, False, (-1), '', False)
        self.zeromq_pub_sink_0 = zeromq.pub_sink(gr.sizeof_char, 1, 'tcp://127.0.0.1:38211', 100, False, (-1), '', True, True)
        self.satellites_pdu_length_filter_0 = satellites.pdu_length_filter(40, 255)
        self.satellites_pdu_head_tail_0 = satellites.pdu_head_tail(3, 16)
        self.satellites_nrzi_decode_0 = satellites.nrzi_decode()
        self.satellites_hdlc_deframer_0 = satellites.hdlc_deframer(check_fcs=True, max_length=10000)
        self.satellites_fsk_demodulator_0 = satellites.components.demodulators.fsk_demodulator(baudrate = baud_rate, samp_rate = samp_rate, iq = True, subaudio = False, options="")
        self.satellites_decode_rs_ccsds_0 = satellites.decode_rs(False, 1)
        self.qtgui_waterfall_sink_x_0 = qtgui.waterfall_sink_c(
            512, #size
            window.WIN_BLACKMAN_hARRIS, #wintype
            0, #fc
            samp_rate, #bw
            "OPS-SAT UHF BEACON", #name
            1, #number of inputs
            None # parent
        )
        self.qtgui_waterfall_sink_x_0.set_update_time(0.1)
        self.qtgui_waterfall_sink_x_0.enable_grid(False)
        self.qtgui_waterfall_sink_x_0.enable_axis_labels(True)



        labels = ['', '', '', '', '',
                  '', '', '', '', '']
        colors = [0, 0, 0, 0, 0,
                  0, 0, 0, 0, 0]
        alphas = [1.0, 1.0, 1.0, 1.0, 1.0,
                  1.0, 1.0, 1.0, 1.0, 1.0]

        for i in range(1):
            if len(labels[i]) == 0:
                self.qtgui_waterfall_sink_x_0.set_line_label(i, "Data {0}".format(i))
            else:
                self.qtgui_waterfall_sink_x_0.set_line_label(i, labels[i])
            self.qtgui_waterfall_sink_x_0.set_color_map(i, colors[i])
            self.qtgui_waterfall_sink_x_0.set_line_alpha(i, alphas[i])

        self.qtgui_waterfall_sink_x_0.set_intensity_range(-140, 10)

        self._qtgui_waterfall_sink_x_0_win = sip.wrapinstance(self.qtgui_waterfall_sink_x_0.qwidget(), Qt.QWidget)

        self.top_layout.addWidget(self._qtgui_waterfall_sink_x_0_win)
        self.pdu_tagged_stream_to_pdu_0 = pdu.tagged_stream_to_pdu(gr.types.byte_t, 'packet_len')
        self.pdu_pdu_to_tagged_stream_1 = pdu.pdu_to_tagged_stream(gr.types.byte_t, 'packet_len')
        self.pdu_pdu_to_tagged_stream_0 = pdu.pdu_to_tagged_stream(gr.types.byte_t, 'packet_len')
        self.digital_descrambler_bb_0 = digital.descrambler_bb(0x21, 0x0, 16)
        self.digital_binary_slicer_fb_0 = digital.binary_slicer_fb()
        self.digital_additive_scrambler_bb_0 = digital.additive_scrambler_bb(0xA9, 0xFF, 7, count=0, bits_per_byte=1, reset_tag_key='packet_len')
        self.blocks_unpacked_to_packed_xx_0 = blocks.unpacked_to_packed_bb(1, gr.GR_MSB_FIRST)
        self.blocks_packed_to_unpacked_xx_0 = blocks.packed_to_unpacked_bb(1, gr.GR_MSB_FIRST)
        self.blocks_message_debug_0 = blocks.message_debug(True, gr.log_levels.info)


        ##################################################
        # Connections
        ##################################################
        self.msg_connect((self.pdu_tagged_stream_to_pdu_0, 'pdus'), (self.satellites_pdu_length_filter_0, 'in'))
        self.msg_connect((self.satellites_decode_rs_ccsds_0, 'out'), (self.blocks_message_debug_0, 'print'))
        self.msg_connect((self.satellites_decode_rs_ccsds_0, 'out'), (self.pdu_pdu_to_tagged_stream_1, 'pdus'))
        self.msg_connect((self.satellites_hdlc_deframer_0, 'out'), (self.satellites_pdu_head_tail_0, 'in'))
        self.msg_connect((self.satellites_pdu_head_tail_0, 'out'), (self.pdu_pdu_to_tagged_stream_0, 'pdus'))
        self.msg_connect((self.satellites_pdu_length_filter_0, 'out'), (self.satellites_decode_rs_ccsds_0, 'in'))
        self.connect((self.blocks_packed_to_unpacked_xx_0, 0), (self.digital_additive_scrambler_bb_0, 0))
        self.connect((self.blocks_unpacked_to_packed_xx_0, 0), (self.pdu_tagged_stream_to_pdu_0, 0))
        self.connect((self.digital_additive_scrambler_bb_0, 0), (self.blocks_unpacked_to_packed_xx_0, 0))
        self.connect((self.digital_binary_slicer_fb_0, 0), (self.satellites_nrzi_decode_0, 0))
        self.connect((self.digital_descrambler_bb_0, 0), (self.satellites_hdlc_deframer_0, 0))
        self.connect((self.pdu_pdu_to_tagged_stream_0, 0), (self.blocks_packed_to_unpacked_xx_0, 0))
        self.connect((self.pdu_pdu_to_tagged_stream_1, 0), (self.zeromq_pub_sink_0, 0))
        self.connect((self.satellites_fsk_demodulator_0, 0), (self.digital_binary_slicer_fb_0, 0))
        self.connect((self.satellites_nrzi_decode_0, 0), (self.digital_descrambler_bb_0, 0))
        self.connect((self.zeromq_sub_source_0, 0), (self.qtgui_waterfall_sink_x_0, 0))
        self.connect((self.zeromq_sub_source_0, 0), (self.satellites_fsk_demodulator_0, 0))


    def closeEvent(self, event):
        self.settings = Qt.QSettings("GNU Radio", "os_demod_decode")
        self.settings.setValue("geometry", self.saveGeometry())
        self.stop()
        self.wait()

        event.accept()

    def get_samp_rate(self):
        return self.samp_rate

    def set_samp_rate(self, samp_rate):
        self.samp_rate = samp_rate
        self.set_gaussian_taps(firdes.gaussian (1.5, 2* (self.samp_rate / self.baud_rate) , 0.5, 12))
        self.qtgui_waterfall_sink_x_0.set_frequency_range(0, self.samp_rate)

    def get_baud_rate(self):
        return self.baud_rate

    def set_baud_rate(self, baud_rate):
        self.baud_rate = baud_rate
        self.set_gaussian_taps(firdes.gaussian (1.5, 2* (self.samp_rate / self.baud_rate) , 0.5, 12))

    def get_gaussian_taps(self):
        return self.gaussian_taps

    def set_gaussian_taps(self, gaussian_taps):
        self.gaussian_taps = gaussian_taps

    def get_gain_mu(self):
        return self.gain_mu

    def set_gain_mu(self, gain_mu):
        self.gain_mu = gain_mu




def main(top_block_cls=os_demod_decode, options=None):

    qapp = Qt.QApplication(sys.argv)

    tb = top_block_cls()

    tb.start()

    tb.show()

    def sig_handler(sig=None, frame=None):
        tb.stop()
        tb.wait()

        Qt.QApplication.quit()

    signal.signal(signal.SIGINT, sig_handler)
    signal.signal(signal.SIGTERM, sig_handler)

    timer = Qt.QTimer()
    timer.start(500)
    timer.timeout.connect(lambda: None)

    qapp.exec_()

if __name__ == '__main__':
    main()
