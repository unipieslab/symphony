vim /etc/systemd/system/rpyc.service 
systemctl daemon-reload && systemctl restart rpyc.service && systemctl status rpyc.service && journalctl -u rpyc.service -n -f

