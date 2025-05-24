from asyncio import Semaphore, TaskGroup
from pathlib import Path
from random import Random
from typing import override

from reactivity import State, batch, memoized_property
from rich import get_console
from rich.panel import Panel
from rich.text import Text

from impl.metadata import cache
from impl.pdf import fetch_pdf
from impl.task import Article
from utils.concurrency import throttle
from utils.ui import UI, rendering

total = min(100, len(cache))

random = Random(42)

choices = [Article(Article.cache[unique_id].metadata) for unique_id in random.sample(list(cache), total)]

sem = Semaphore(10)

console = get_console()

(output_dir := Path("data/articles")).mkdir(parents=True, exist_ok=True)


class App(UI):
    success = State(0)
    failed = State(0)

    last_success = State()

    @memoized_property
    def completed(self):
        return self.success + self.failed

    @override
    def render(self):
        status_text = Text()
        status_text.append(f"Total: {total} ", style="dim")
        status_text.append(f"Success: {self.success} ", style="green")
        status_text.append(f"Failed: {self.failed}", style="red")
        if self.last_success:
            status_text.append(f"\nLast Success: {self.last_success}")

        return Panel(status_text, title=f"Downloading: ({self.completed / total:.1%})", border_style="cyan", expand=False, title_align="left")

    async def download_all(self):
        async with TaskGroup() as tg:
            for article in choices:
                tg.create_task(self.download_one(article))

    @throttle(10)
    async def download_one(self, article: Article):
        output_path = output_dir / f"{article.unique_id.replace(':', '_')}.pdf"
        if output_path.is_file():
            with batch():
                self.last_success = article.unique_id
                self.success += 1
                return

        try:
            info = await article.get_info(sem)
            if url := info.pdf_url:
                if url.startswith("//"):
                    url = f"https:{url}"
                elif url.startswith("/"):
                    self.failed += 1
                    return
                output_path.write_bytes(await fetch_pdf(url))
                with batch():
                    self.last_success = article.unique_id
                    self.success += 1
            else:
                self.failed += 1

        except Exception as e:
            console.print(f"Error downloading {article.key}: {e!s}")
            self.failed += 1


if __name__ == "__main__":
    from asyncio import run

    async def main():
        with rendering(ctx := App()):
            await ctx.download_all()

    run(main())
