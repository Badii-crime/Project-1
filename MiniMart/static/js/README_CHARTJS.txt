This folder is where chart.umd.min.js goes (Chart.js, used by the dashboard).

To make the dashboard graphs work fully OFFLINE, download the file once
(needs internet the first time only) and save it right here as:

    static/js/chart.umd.min.js

Direct download link:
    https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.0/chart.umd.min.js

Steps:
1. Open that link in your browser.
2. Right-click the page -> "Save As" (or Ctrl+S).
3. Save it as "chart.umd.min.js" inside this static/js/ folder
   (same folder as script.js).
4. Refresh the Dashboard page - the graphs will now work even without
   internet.

If you skip this step, the app will still try to load Chart.js from the
internet automatically when the Dashboard page opens, so the graphs will
still work as long as you have an internet connection at that moment.
