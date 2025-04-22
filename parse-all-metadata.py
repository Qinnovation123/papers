from asyncio import Semaphore, TaskGroup

from reactivity import State
from rich import get_console

from impl.metadata import get_metadata
from impl.task import Article, articles
from utils.concurrency import throttle
from utils.ui import UI, rendering

total = len(articles)

sem = Semaphore(5)

console = get_console()


class App(UI):
    completed = State(0)
    success = State(0)
    failed = State(0)

    last_success = State()

    def render(self):
        from rich.panel import Panel
        from rich.text import Text

        status_text = Text()
        status_text.append(f" Total: {total}", style="dim")
        status_text.append(f" Completed: {self.completed} ({self.completed / total:.1%})", style="cyan")
        status_text.append(f" Success: {self.success}", style="green")
        status_text.append(f" Failed: {self.failed}", style="red")
        if self.last_success:
            status_text.append(f"\n Last Success: {self.last_success}")

        return Panel(status_text, title="PDF Download Progress", border_style="green")

    async def parse_all(self):
        async with TaskGroup() as tg:
            for article in articles:
                tg.create_task(self.parse_one(article))

    @throttle(100)
    async def parse_one(self, article: Article):
        try:
            metadata = await get_metadata(article)
            if metadata:
                self.last_success = article.unique_id
                self.success += 1
            else:
                self.failed += 1
        except Exception as e:
            console.print(f"Error downloading {article.key}: {e!s}")
            self.failed += 1
        finally:
            self.completed += 1


if __name__ == "__main__":
    from asyncio import run

    async def main():
        with rendering(ctx := App()):
            await ctx.parse_all()

    run(main())
