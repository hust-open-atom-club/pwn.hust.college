#!/bin/sh

XML=/home/hacker/.config/xfce4/xfconf/xfce-perchannel-xml/xfce4-panel.xml

for LAUNCHER in /home/hacker/.config/xfce4/panel/launcher-*
do
        NUMBER=${LAUNCHER##*-}
        EXE=$(cat "$LAUNCHER"/*.desktop | grep Exec | sed -e "s/.*=//")
        if [ ! -f "$EXE" ] && ! printf '%s' "$EXE" | grep -q " "
        then
                rm -rf "$LAUNCHER"
                # Delete the launcher's plugin property block. sed range
                # matching stops at the first </property>, which is the
                # closing tag of a nested property, leaving a stray tag and
                # corrupting the XML; track nesting depth instead.
                awk -v plugin="plugin-$NUMBER" '
                        $0 ~ "<property name=\"" plugin "\" type=\"string\" value=\"launcher\">" {
                                skipping = 1
                                depth = 1
                                next
                        }
                        skipping {
                                opens = gsub(/<property/, "<property")
                                selfclosing = gsub(/<property[^>]*\/>/, "<property")
                                closes = gsub(/<\/property>/, "</property>")
                                depth += opens - selfclosing - closes
                                if (depth <= 0)
                                        skipping = 0
                                next
                        }
                        { print }
                ' "$XML" > "$XML.new" && mv "$XML.new" "$XML"
        fi
done
