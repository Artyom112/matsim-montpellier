package org.matsim.project;

import org.matsim.core.api.experimental.events.EventsManager;
import org.matsim.core.events.EventsUtils;
import org.matsim.core.events.MatsimEventsReader;

import java.io.PrintWriter;

public class RunHourlyVolumes {
    public static void main(String[] args) throws Exception {
        String eventsFile = "output_200/output_events.xml.zst";   // путь от корня проекта
        String outFile    = "output_200/hourly_link_volumes.csv";

        EventsManager events = EventsUtils.createEventsManager();
        HourlyLinkVolumeHandler handler = new HourlyLinkVolumeHandler();
        events.addHandler(handler);

        events.initProcessing();
        new MatsimEventsReader(events).readFile(eventsFile);
        events.finishProcessing();

        try (PrintWriter w = new PrintWriter(outFile)) {
            w.print("link");
            for (int h = 0; h < 24; h++) w.print(",h" + h);
            w.println();
            handler.getVolumes().forEach((linkId, counts) -> {
                w.print(linkId);
                for (int c : counts) w.print("," + c);
                w.println();
            });
        }
        System.out.println("Готово: " + outFile);
    }
}