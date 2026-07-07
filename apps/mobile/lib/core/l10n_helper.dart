import 'package:flutter/material.dart';
import 'package:intl/intl.dart';

class L10nHelper {
  static final currency =
      NumberFormat.currency(locale: 'en_IN', symbol: '₹', decimalDigits: 0);
  static final date = DateFormat.yMMMd('en_IN');

  static String t(BuildContext context, String key, {String fallback = ''}) {
    // flutter_i18n can be wired; ARB assets exist under assets/i18n/
    return fallback.isNotEmpty ? fallback : key;
  }
}
