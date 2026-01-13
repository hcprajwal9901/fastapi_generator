export default function Header() {
    return (
        <header className="space-y-2">
            <h1 className="text-4xl font-extrabold bg-gradient-to-r from-blue-400 to-emerald-400 bg-clip-text text-transparent">
                FastAPI Generator v2.0
            </h1>
            <p className="text-white/60">
                Deterministic backend generation using Jinja2 templates and strict CPS validation.
            </p>
        </header>
    );
}
