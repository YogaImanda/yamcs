import { Component } from '@angular/core';
import { Title } from '@angular/platform-browser';
import { YamcsService } from '../../core/services/YamcsService';
import { MessageService } from '../../core/services/message.service';
import { TimelineItem } from '../../shared/TimelineItem';

@Component({
  selector: 'app-scheduled-scripts',
  templateUrl: './scheduled-script.component.html',
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

    // contoh: ambil item dari 1 hari ke belakang sampai 30 hari ke depan
    const start = new Date(now.getTime() - 24 * 60 * 60 * 1000).toISOString();
    const stop  = new Date(now.getTime() + 30 * 24 * 60 * 60 * 1000).toISOString();

    console.log('[ScheduledScripts] load()', { start, stop, instance: this.yamcs.instance });

    this.yamcs.yamcsClient
      .getTimelineItems(this.yamcs.instance!, { start, stop } as any)
      .then(page => {
        console.log('[ScheduledScripts] page', page);

        this.items = (page.items || []).filter(item =>
          item.type === 'ACTIVITY' &&
          item.activityDefinition &&                       // punya activity definition
          item.activityDefinition.type === 'PROC'          // sesuaikan filter kamu
          // atau bisa cek tag: item.tags?.includes('SCHEDULED')
        );
      })
      .catch(err => {
        console.error('[ScheduledScripts] error', err);
        this.messageService.showError(err);
      })
      .finally(() => {
        this.loading = false;      // ⬅️ PENTING: selalu matikan loading di sini
      });
  }
}
