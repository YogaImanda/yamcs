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

  /**
   * Ambil daftar scheduled script dari REST API timeline.
   */
  load() {
    this.loading = true;
    this.lastError = undefined;

    const instance = this.yamcs.instance!;
    const now = new Date();

    // jendela waktu: 1 hari ke belakang s/d 30 hari ke depan
    const start = new Date(now.getTime() - 24 * 60 * 60 * 1000).toISOString();
    const stop  = new Date(now.getTime() + 30 * 24 * 60 * 60 * 1000).toISOString();

    const params = new URLSearchParams({
      start,
      stop,
      detail: 'true',
    });

    const url = `/api/timeline/${encodeURIComponent(instance)}/items?${params.toString()}`;
    console.log('[ScheduledScripts] fetch URL =', url);

    try {
      const fetchFn: any = (window as any).fetch;

      if (typeof fetchFn !== 'function') {
        const msg = 'window.fetch tidak tersedia di browser ini';
        console.error('[ScheduledScripts] ' + msg);
        this.lastError = msg;
        this.loading = false;
        return;
      }

      fetchFn(url, { credentials: 'same-origin' })
        .then((response: Response) => {
          if (!response.ok) {
            throw new Error(`HTTP ${response.status} ${response.statusText}`);
          }
          return response.json();
        })
        .then((json: any) => {
          console.log('[ScheduledScripts] raw response:', json);

          const allItems = json?.items || [];

          // Filter: hanya activity SCRIPT yang statusnya future (PLANNED/SCHEDULED/PENDING)
          this.items = allItems.filter((item: any) => {
            const type = (item.type || '').toUpperCase();
            const detailType = (item.detail?.type || '').toUpperCase();
            const status =
              (item.executionStatus ||
               item.detail?.executionStatus ||
               '').toUpperCase();

            const isScript =
              type === 'SCRIPT' ||
              detailType === 'SCRIPT';

            const isPlanned =
              status === 'PLANNED' ||
              status === 'SCHEDULED' ||
              status === 'PENDING';

            return isScript && isPlanned;
          });

          console.log('[ScheduledScripts] filtered items:', this.items);
          this.loading = false;
        })
        .catch((err: any) => {
          console.error('[ScheduledScripts] async error:', err);
          this.lastError = err?.message || String(err);
          this.messageService.showError(err);
          this.loading = false;
        });

    } catch (e: any) {
      console.error('[ScheduledScripts] sync error:', e);
      this.lastError = e?.message || String(e);
      this.loading = false;
    }
  }
}
