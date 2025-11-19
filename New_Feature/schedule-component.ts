import { ChangeDetectionStrategy, Component } from '@angular/core';
import { Title } from '@angular/platform-browser';
import {
  MessageService,
  WebappSdkModule,
  YamcsService,
  TimelineItem,
} from '@yamcs/webapp-sdk';
import { AsyncPipe, DatePipe, NgForOf, NgIf } from '@angular/common';

@Component({
  templateUrl: './scheduled-scripts.component.html',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [WebappSdkModule, NgForOf, NgIf, AsyncPipe, DatePipe],
})
export class ScheduledScriptsComponent {

  items: TimelineItem[] = [];
  loading = true;

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
    const start = now.toISOString();
    // misal 30 hari ke depan
    const stop = new Date(now.getTime() + 30 * 24 * 60 * 60 * 1000).toISOString();

    this.yamcs.yamcsClient.getTimelineItems(this.yamcs.instance!, {
      start,
      stop,
      type: 'ACTIVITY',
    })
      .then(page => {
        this.items =
          (page.items || []).filter(item =>
            item.activity && item.activity.type === 'SCRIPT'
          );
        this.loading = false;
      })
      .catch(err => {
        this.messageService.showError(err);
        this.loading = false;
      });
  }

  // (opsional) nanti bisa ditambah fungsi delete/cancel di sini
}
