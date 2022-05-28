#!/usr/bin/env python
import os
import sys
import json
import psutil
import socket
import logging
import subprocess

from datetime import datetime
from telegram.ext import Updater, CommandHandler
from telegram.ext import MessageHandler, Filters

RDP_ARGS = ['on', 'off', 'check']
BASE_DIR = os.path.dirname(sys.argv[0])
LOG_FILE = os.path.join(BASE_DIR, "rdc-bot.log")
CONF_FILE = os.path.join(BASE_DIR, "rdc-bot.conf")

logging.basicConfig(filename=LOG_FILE, format='%(asctime)s - RDCBot - %(levelname)s - %(message)s',
                    level=logging.INFO, datefmt='%Y-%m-%d %H:%M:%S')

mess = {
    "error_param": "Tham số không hợp lệ",
    "error_fw_off": "Vui lòng BẬT Windows Firewall",
    "success_vpn_on": "Đã bật VPN",
    "success_vpn_off": "Đã tắt VPN",
    "error_vpn_running": "VPN không hoạt động"
}


def unix_to_datetime(unix_ts: float):
    """ Convert unix timestamp to datetime """
    return datetime.fromtimestamp(unix_ts)


def rdc_init():
    try:
        with open(CONF_FILE, 'r') as f:
            conf = json.load(f)
        return conf
    except Exception as ex:
        logging.info('rdc_init: %s' % str(ex))
    return None


def bot_banner(update, context):
    markdown_text = "`{0} BẢNG ĐIỀU KHIỂN {0}`\n".format(':' * 10)
    markdown_text += "`/rdp on         : Cho phép kết nối RDP`\n"
    markdown_text += "`/rdp off        : Từ chối kết nối RDP`\n"
    markdown_text += "`/rdp check      : Kiểm tra trạng thái RDP`\n"
    markdown_text += "`/vpn on         : Kết nối VPN`\n"
    markdown_text += "`/vpn off        : Ngắt kết nối VPN`\n"
    markdown_text += "`/vpn check      : Kiểm tra trạng thái VPN`\n\n"
    markdown_text += "`Remote Desktop Control Bot v1.0.3`\n"
    update.message.reply_text(markdown_text, parse_mode='MarkdownV2')


def message_format(mes):
    return "`{}`".format(mes)


def error_handler(update, context):
    logging.warning('Update "%s" caused error "%s"', update, context.error)


def echo_message(update, context):
    conf = rdc_init()
    chat_id = str(update.message.chat_id)
    if chat_id != conf.get('chat_id'):
        return
    bot_banner(update, context)


def get_process_by_name(proc_name):
    try:
        proc_data = []
        attrs = ['pid', 'name', 'status', 'create_time', 'username', 'cmdline']
        procs = psutil.process_iter(attrs, ad_value=None)
        for proc in procs:
            if proc.info["name"] == proc_name:
                proc_data = proc.info
        return proc_data
    except Exception as ex:
        logging.info('get_process_by_name: %s' % str(ex))


def get_network_info():
    try:
        network_info = list()
        for interface, snicaddrs in psutil.net_if_addrs().items():
            if len(snicaddrs) > 2:
                temp = dict()
                temp['interface'] = interface
                for snic in snicaddrs:
                    if snic.family == socket.AF_INET:
                        temp['ipv4'] = snic.address
                    elif snic.family == socket.AF_INET6:
                        temp['ipv6'] = snic.address
                    else:
                        temp['mac_address'] = snic.address
                network_info.append(temp)
        return network_info
    except Exception as ex:
        logging.info('get_network_info: %s' % str(ex))


def kill_process_by_name(proc_name):
    try:
        for proc in psutil.process_iter():
            if proc.name() == proc_name:
                proc.kill()
    except Exception as ex:
        logging.info('kill_process_by_name: %s' % str(ex))


def vpn_on(update, context):
    try:
        conf = rdc_init()
        proc_name = os.path.basename(conf.get("openvpn_bin"))
        kill_process_by_name(proc_name)
        process = subprocess.Popen([conf.get("openvpn_bin"), "--config", conf.get("openvpn_config")], shell=True,
                                   stdin=subprocess.DEVNULL, stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
        update.message.reply_text(message_format(mess.get('success_vpn_on')), parse_mode='MarkdownV2')
        logging.warning('vpn_status: On')
    except Exception as ex:
        logging.info('vpn_on: %s' % str(ex))


def vpn_off(update, context):
    try:
        conf = rdc_init()
        proc_name = os.path.basename(conf.get("openvpn_bin"))
        kill_process_by_name(proc_name)
        update.message.reply_text(message_format(mess.get('success_vpn_off')), parse_mode='MarkdownV2')
        logging.warning('vpn_status: Off')
    except Exception as ex:
        logging.info('vpn_off: %s' % str(ex))


def vpn_check(update, context):
    try:
        tmp = dict()
        conf = rdc_init()
        proc_name = os.path.basename(conf.get("openvpn_bin"))
        proc_info = get_process_by_name(proc_name)
        if not proc_info:
            update.message.reply_text(message_format(mess.get('error_vpn_running')), parse_mode='MarkdownV2')
            return
        proc_info['cmdline'] = " ".join(proc_info['cmdline'])
        proc_info['create_time'] = unix_to_datetime(proc_info['create_time']).strftime('%Y-%m-%d %H:%M:%S')
        net_info = get_network_info()
        net_text = json.dumps(net_info, indent=4, sort_keys=False)
        proc_text = json.dumps(proc_info, indent=4, sort_keys=False)
        update.message.reply_text(message_format(net_text), parse_mode='MarkdownV2')
        logging.info('vpn_check: %s' % str(proc_info))
        update.message.reply_text(message_format(proc_text), parse_mode='MarkdownV2')
        logging.info('vpn_check: %s' % str(net_info))
    except Exception as ex:
        logging.info('vpn_check: %s' % str(ex))


def vpn_handler(update, context):
    try:
        if command_validator(update, context):
            cmd = str(context.args[0])
            return {
                'on': vpn_on,
                'off': vpn_off,
                'check': vpn_check
            }.get(cmd)(update, context)
    except Exception as ex:
        logging.info('vpn_handler: %s' % str(ex))


def adv_firewall_status():
    """
    Control Panel > System and Security > Windows Defender Firewall
    Private Networks: Networks at home or work where you know and trust the people and devices on the network
    :return (Boolean). True: Firewall is ON, False: Firewall is OFF
    Problem with Subprocess and fix: https://stackoverflow.com/a/40108817, https://stackoverflow.com/a/43606682
    """
    try:
        # netsh advfirewall show /?
        state = subprocess.check_output('netsh advfirewall show privateprofile state', stdin=subprocess.DEVNULL,
                                        stderr=subprocess.DEVNULL).decode('utf-8')
        return state.count('ON') == 1
    except Exception as ex:
        logging.info('adv_firewall_status: %s' % str(ex))
    return False


def adv_firewall_rdp_status():
    try:
        fw_status = {}
        fw_rules = {
            'rdp_shadow_in': 'netsh advfirewall firewall show rule name="Remote Desktop - Shadow (TCP-In)"',
            'rdp_tcp_in': 'netsh advfirewall firewall show rule name="Remote Desktop - User Mode (TCP-In)"',
            'rdp_udp_in': 'netsh advfirewall firewall show rule name="Remote Desktop - User Mode (UDP-In)"'
        }
        for name, cmd in fw_rules.items():
            output = subprocess.check_output(cmd, stdin=subprocess.DEVNULL, stderr=subprocess.DEVNULL).decode('utf-8')
            tmp = output.split('\r\n')[3].replace(' ', '')
            fw_status[name] = tmp.split(':')[-1]
        return fw_status
    except Exception as ex:
        logging.info('adv_firewall_rdp_status: %s' % str(ex))
    return None


def adv_firewall_rdp_control(enable=True):
    """
    Ref: https://docs.microsoft.com/en-us/troubleshoot/windows-server/networking/netsh-advfirewall-firewall-control-firewall-behavior
    - netsh advfirewall firewall set rule group="remote desktop" new enable=Yes
    - netsh advfirewall firewall set rule group="remote desktop" new enable=No
    """
    try:
        cmd = 'netsh advfirewall firewall set rule group="remote desktop" new enable='
        if enable:
            cmd += 'Yes'
        else:
            cmd += 'No'
        output = subprocess.check_output(cmd, stdin=subprocess.DEVNULL, stderr=subprocess.DEVNULL).decode('utf-8')
        return output.replace('\r\n', '')
    except Exception as ex:
        logging.info('adv_firewall_rdp_control: %s' % str(ex))
    return None


def command_validator(update, context):
    try:
        conf = rdc_init()
        chat_id = str(update.message.chat_id)
        if chat_id != conf.get('chat_id'):
            return False
        args_len = len(context.args)
        if args_len == 0:
            bot_banner(update, context)
            return False
        elif args_len == 1:
            arg_0 = str(context.args[0])
            if arg_0 not in RDP_ARGS:
                update.message.reply_text(message_format(mess.get('error_param')), parse_mode='MarkdownV2')
                return False
        else:
            update.message.reply_text(message_format(mess.get('error_param')), parse_mode='MarkdownV2')
            return False
    except Exception as ex:
        logging.info('command_validator: %s' % str(ex))
    return True


def rdp_handler(update, context):
    try:
        if command_validator(update, context):
            cmd = str(context.args[0])
            return {
                'on': rdp_on,
                'off': rdp_off,
                'check': rdp_check
            }.get(cmd)(update, context)
    except Exception as ex:
        logging.info('rdp_handler: %s' % str(ex))


def rdp_on(update, context):
    try:
        if not adv_firewall_status():
            update.message.reply_text(message_format(mess.get('error_fw_off')), parse_mode='MarkdownV2')
            return
        result = adv_firewall_rdp_control(enable=True)
        update.message.reply_text(message_format(result), parse_mode='MarkdownV2')
        logging.warning('rdp_on: Ok')
    except Exception as ex:
        logging.info('rdp_on: %s' % str(ex))


def rdp_off(update, context):
    try:
        if not adv_firewall_status():
            update.message.reply_text(message_format(mess.get('error_fw_off')), parse_mode='MarkdownV2')
            return
        result = adv_firewall_rdp_control(enable=False)
        update.message.reply_text(message_format(result), parse_mode='MarkdownV2')
        logging.warning('rdp_off: Ok')
    except Exception as ex:
        logging.info('rdp_off: %s' % str(ex))


def rdp_check(update, context):
    try:
        if not adv_firewall_status():
            update.message.reply_text(message_format(mess.get('error_fw_off')), parse_mode='MarkdownV2')
            return
        result = adv_firewall_rdp_status()
        tmp = result
        result = json.dumps(result, sort_keys=False, indent=4)
        update.message.reply_text(message_format(result), parse_mode='MarkdownV2')
        logging.info('rdp_check: %s' % str(tmp))
    except Exception as ex:
        logging.info('rdp_check: %s' % str(ex))


def rdc_bot():
    conf = rdc_init()
    bot_token = conf.get('bot_token')
    updater = Updater(bot_token, use_context=True)
    dp = updater.dispatcher
    command_handler = {
        'help': echo_message,
        'rdp': rdp_handler,
        'vpn': vpn_handler
    }
    for command, handler in command_handler.items():
        dp.add_handler(CommandHandler(command, handler))
    dp.add_handler(MessageHandler(Filters.text, echo_message))
    dp.add_error_handler(error_handler)
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    rdc_bot()
