# Telegram QSO logging bot

This Telegram bot logs every callsign sent to him into a personal logbook which you can later download in ADIF format.

## Why?

I was annoyed by my own bad habit - taking notes of my radio contacts on the Telegram's "Saved Messages" section.

## Can I try it myself?

Yes please. Talk to [@qso_log_bot](https://t.me/qso_log_bot). Don't forget to set your `/station_callsign` before doing any logging. If your Telegram username looks like a ham radio callsign, the bot will use that for your station callsign.

## Bot features
* Automatic logging of callsigns 
* Deletion of last QSO
* Inline changing of bands, modes
* Download your log in ADIF format
* `TODO`: exchanges!
* `TODO`: contests!

## Command reference

Type in any callsign and the bot will log the contact at current date/time. Also, inline mode and band changes are supported - just type `80m` or `ssb` and new contacts will be logged in this band/mode.

* `/start` - Get started!
* `/help` - Get help on usage
* `/station_callsign` - Set your station callsign
* `/adif` - Download your log in ADIF format
* `/del` - Delete last QSO from log
* `/mode` - Set radio operating mode (but easier to use inline, i.e. type `cw`)
* `/band` - Set radio band (command not implemented, just type `80m` inline)

## Author

Simonas Kareiva LY2EN <ly2en@qrz.lt>