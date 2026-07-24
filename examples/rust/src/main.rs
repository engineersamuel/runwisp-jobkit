use std::{env, process};

fn main() {
    let args: Vec<String> = env::args().skip(1).collect();
    let dry_run = match args.as_slice() {
        [] => false,
        [argument] if argument == "--dry-run" => true,
        _ => {
            eprintln!("usage: cargo run --quiet -- [--dry-run]");
            process::exit(2);
        }
    };
    let message = env::var("RUNWISP_EXAMPLE_MESSAGE").expect("message is required");

    if dry_run {
        println!("dry-run: {message}");
    } else {
        println!("{message}");
    }
}
