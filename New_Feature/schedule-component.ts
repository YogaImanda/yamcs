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
  lastError?: string;

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
    this.lastError = undefined;

    const now = new Date();
    const start = new Date(now.getTime() - 24 * 60 * 60 * 1000).toISOString();  // 1 hari ke belakang
    const stop  = new Date(now.getTime() + 30 * 24 * 60 * 60 * 1000).toISOString(); // 30 hari ke depan

    console.log('[ScheduledScripts] load()', {
      instance: this.yamcs.instance,
      start,
      stop,
    });

    try {
      const client: any = this.yamcs.yamcsClient;
      if (!client || typeof client.getTimelineItems !== 'function') {
        const msg = 'yamcsClient.getTimelineItems() tidak tersedia';
        console.error('[ScheduledScripts] ' + msg, client);
        this.lastError = msg;
        this.loading = false;
        return;
      }

      client.getTimelineItems(this.yamcs.instance!, { start, stop })
        .then((page: any) => {
          console.log('[ScheduledScripts] page', page);
          this.items = page?.items || [];
        })
        .catch((err: any) => {
          console.error('[ScheduledScripts] error from API', err);
          this.lastError = (err && err.message) ? err.message : String(err);
          this.messageService.showError(err);
        })
        .finally(() => {
          this.loading = false;
          console.log('[ScheduledScripts] done, loading =', this.loading,
            'items =', this.items?.length);
        });
    } catch (e: any) {
      console.error('[ScheduledScripts] synchronous error', e);
      this.lastError = (e && e.message) ? e.message : String(e);
      this.loading = false;
    }
  }
}
