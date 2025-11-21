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
   * Load daftar script yang DISCHEDULE dari REST API timeline.
   * Kita pakai window.fetch supaya tidak tergantung method khusus di YamcsClient.
   */
  load() {
    this.loading = true;
    this.lastError = undefined;

    const instance = this.yamcs.instance!;
    const now = new Date();

    // jendela waktu: 1 hari ke belakang sampai 30 hari ke depan
    const start = new Date(now.getTime() - 24 * 60 * 60 * 1000).toISOString();
    const stop  = new Date(now.getTime() + 30 * 24 * 60 * 60 * 1000).toISOString();

    const params = new URLSearchParams({
      start,
      stop,
      // detail=true supaya field-field tambahan (detail, executionStatus, dll) ikut dikirim
      detail: 'true',
    });

    const url = `/api/timeline/${encodeURIComponent(instance)}/items?${params.toString()}`;

    console.log('[ScheduledScripts] fetching', url);

    // pakai window.fetch agar TypeScript mengenali fungsi ini
    window.fetch(url, {
      credentials: 'same-origin', // kirim cookie session yamcs
    })
      .then(response => {
        if (!response.ok) {
          throw new Error(`HTTP ${response.status} ${response.statusText}`);
        }
        return response.json();
      })
      .then(json => {
        console.log('[ScheduledScripts] raw response', json);

        const allItems = json?.items || [];

        // Filter hanya activity yang terkait SCRIPT dan statusnya future (PLANNED/SCHEDULED/PENDING)
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

        console.log('[ScheduledScripts] filtered items', this.items);
      })
      .catch(err => {
        console.error('[ScheduledScripts] error', err);
        this.lastError = err?.message || String(err);
        this.messageService.showError(err);
      })
      .finally(() => {
        this.loading = false;
        console.log(
          '[ScheduledScripts] DONE loading=',
          this.loading,
          'items=',
          this.items.length,
          'error=',
          this.lastError,
        );
      });
  }
}
