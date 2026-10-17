package org.matsim.project;

import org.matsim.api.core.v01.Id;
import org.matsim.api.core.v01.events.LinkEnterEvent;
import org.matsim.api.core.v01.events.handler.LinkEnterEventHandler;
import org.matsim.api.core.v01.network.Link;
import java.util.HashMap;
import java.util.Map;

public class HourlyLinkVolumeHandler implements LinkEnterEventHandler {
    private final Map<Id<Link>, int[]> volumes = new HashMap<>();

    @Override
    public void handleEvent(LinkEnterEvent event) {
        int hour = (int) (event.getTime() / 3600.0);
        if (hour < 0 || hour > 23) return; // события после полуночи
        volumes.computeIfAbsent(event.getLinkId(), k -> new int[24])[hour]++;
    }

    @Override
    public void reset(int iteration) {
        volumes.clear(); // обнуление между итерациями
    }

    public Map<Id<Link>, int[]> getVolumes() {
        return volumes;
    }
}