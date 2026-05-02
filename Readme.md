# Ezio

<b>🚧 WIP! This project is not in a working state yet, don't use this right now. 🚧</b>
<hr/>

Display a recorded route as a static website. Take a look at my
[Balkans cycling route](https://projects.pascalsommer.ch/balkanvelo/) to see an 
example output.

![Example image of a rendered route across the balkans](balkanroute.png)

The name is inspired by [Ezio Auditore da Firenze](https://en.wikipedia.org/wiki/Ezio_Auditore_da_Firenze)
because in the Assassin's Creed game series you have to climb towers to uncover
the map. Here in this static site generator, you, uhh.. go cycling and then get
to see a pretty map of it? Pretty much the same thing if you ask me.

## Usage

This tool takes photos and routes as input. All input files should be placed
in an input directory. The tool will check all files in the input directory
including subdirectories, ignore unrecognized files, and load photos and route
data. Only [GPX](https://en.wikipedia.org/wiki/GPS_Exchange_Format) files are
supported for route data for now.

```bash
# Assuming that ./input-directory/ contains your photos and .gpx files
ezio -i input-directory -o output-directory
```

If your GPX files contain more recordings than just the route you want to
display, then you can limit the date range with the following options:

```bash
ezio -i input-directory -o output-directory --start-date 2026-04-21 --end-date 2026-04-23
```

You can optionally add a title to the generated static website:
`--title "My Cool Cycling Trip"`.

The above commands will generate a static website in the output directory, which
you can now copy to your server. Note that the website doesn't work when using
the `file://` protocol, i.e. you cannot just double click the `index.html` file
to open it in your browser.

```bash
# start up a quick webserver to see the result
cd output-directory
python -m http.server

# now open http://localhost:8000 in your browser
```

## Limitations

This program currently assumes that the following constraints hold. The output
is undefined if the data does not follow these constraints.

* Route recordings must not extend across midnight in the active time zone.
* The combined route must not cross the ±180° longitude line.
* The combined route must not cross a time zone boundary.
* The viewer currently highlights route segments by day. No other grouping type
  (weeks / custom / etc.) is currently possible.

Some of these constraints might be relaxed in the future if the need arises.

Note also that time zone handling is tricky for photos because some cameras
store the capture time in local time but don't add time zone information. Feel
free to open an issue if you think that the current handling of times does not
work for your use case or could be improved.

## License

AGPL-3.0-or-later
