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

    const instance = this.yamcs.instance!;
    const processor = this.yamcs.processor!;

    console.log('[ScheduledScripts] API:',
      `/api/processors/${instance}/${processor}/procedures/scheduled`
    );

    this.yamcs.yamcsClient
      .request(
        'GET',
        `/api/processors/${instance}/${processor}/procedures/scheduled`
      )
      .then((response: any) => {
        console.log('[ScheduledScripts] response:', response);
        this.items = response?.entries || [];
      })
      .catch((err: any) => {
        console.error('[ScheduledScripts] error:', err);
        this.lastError = err?.message || String(err);
        this.messageService.showError(err);
      })
      .finally(() => {
        this.loading = false;
        console.log('[ScheduledScripts] DONE loading=', this.loading);
      });
  }
}
