import { ChangeDetectionStrategy, Component } from '@angular/core';
import { Title } from '@angular/platform-browser';

import {
  MessageService,
  WebappSdkModule,
  YamcsService,
} from '@yamcs/webapp-sdk';

@Component({
  selector: 'app-scheduled-scripts',
  templateUrl: './schedule-script.component.html',
  changeDetection: ChangeDetectionStrategy.OnPush,
  standalone: true,
  imports: [WebappSdkModule],
})
export class ScheduledScriptsComponent {

  loading = true;
  items: any[] = [];

  constructor(
    title: Title,
    readonly yamcs: YamcsService,
    private messageService: MessageService,
  ) {
    title.setTitle('Scheduled scripts');
    this.load();
  }

  load() {
    this.loading = true;

    const now = new Date();

    // ambil item timeline dari 1 hari ke belakang sampai 30 hari ke depan
    const start = new Date(now.getTime() - 24 * 60 * 60 * 1000).toISOString();
    const stop  = new Date(now.getTime() + 30 * 24 * 60 * 60 * 1000).toISOString();

    console.log('[ScheduledScripts] load()', {
      instance: this.yamcs.instance,
      start,
      stop,
    });

    this.yamcs.yamcsClient
      .getTimelineItems(this.yamcs.instance!, { start, stop } as any)
      .then(page => {
        console.log('[ScheduledScripts] page', page);

        // Sederhana dulu: tampilkan semua item.
        // Nanti kalau mau, bisa difilter khusus yang related ke script.
        this.items = page.items || [];
      })
      .catch(err => {
        console.error('[ScheduledScripts] error', err);
        this.messageService.showError(err);
      })
      .finally(() => {
        this.loading = false;
      });
  }
}
