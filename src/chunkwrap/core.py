"""Main application logic and coordination for chunkwrap."""

from .file_handler import read_files
from .security import load_trufflehog_regexes, mask_secrets
from .state import read_state, write_state
from .output import create_prompt_text, format_json_wrapper, output_chunk, print_progress_info


class ChunkProcessor:
    """Main processor for handling file chunking and output."""

    def __init__(self, config):
        """Initialize the processor with configuration."""
        self.config = config
        self.regex_patterns = load_trufflehog_regexes()

    # ---------- Budgeted splitting (caps FINAL output length) ----------

    def _measure_wrapped_len(self, prompt_text: str, body: str, idx: int) -> int:
        """
        Return len(final_output) for a candidate body, using a conservative placeholder
        for `total` so we never under-estimate overhead.
        """
        # Worst-case total digits to over-estimate the metadata length a bit.
        # Using a big number prevents final output from ever exceeding --size when we
        # recompute with the real total later.
        probe_info = {
            "index": idx,
            "total": 999_999,          # pessimistic upper bound
            "is_first": idx == 0,
            "is_last": False,          # not used by format_json_wrapper itself; prompt_text already chosen
            "chunk": body,
        }
        wrapped = format_json_wrapper(prompt_text, body, probe_info, self.config_args, self.config)
        return len(wrapped)

    def _best_prompt_for_measure(self, base_prompt, idx, candidate_body):
        """
        Choose the longer of (intermediate prompt) vs (last prompt) so measurement
        is pessimistic and cannot overflow later.
        """
        ci_mid = {"index": idx, "total": 999_999, "is_first": idx == 0, "is_last": False, "chunk": candidate_body}
        ci_last = {"index": idx, "total": 999_999, "is_first": idx == 0, "is_last": True,  "chunk": candidate_body}
        p_mid  = create_prompt_text(base_prompt, self.config, ci_mid,  self.config_args)
        p_last = create_prompt_text(base_prompt, self.config, ci_last, self.config_args)
        return p_mid if len(p_mid) >= len(p_last) else p_last

    def _emit_bodies_budgeted(self, full_text: str, size_limit: int, args):
        """
        Split full_text into a list of raw (unmasked) bodies such that each FINAL wrapped
        output (prompt + JSON + masked content) is <= size_limit.
        No content loss: remainder is carried forward to next chunk.
        """
        self.config_args = args  # stash for measurement helpers

        bodies = []
        remaining = full_text
        idx = 0

        if size_limit <= 0:
            raise ValueError("--size must be positive")

        while remaining:
            # Binary search the maximum prefix length that fits within the size budget.
            lo, hi = 1, len(remaining)
            best_len = 0

            # Precompute the worst-case prompt text once per chunk index.
            # We measure on MASKED content because masking can expand length.
            # We recompute prompt per mid below (it’s independent of body content length).
            # Here we seed with the first char to compute a pessimistic prompt length.
            worst_prompt = self._best_prompt_for_measure(args.prompt, idx, remaining[:1])

            while lo <= hi:
                mid = (lo + hi) // 2
                candidate_raw = remaining[:mid]
                candidate_masked = mask_secrets(candidate_raw, self.regex_patterns)

                # Measure with conservative total and worst-case prompt
                wrapped_len = self._measure_wrapped_len(worst_prompt, candidate_masked, idx)

                if wrapped_len <= size_limit:
                    best_len = mid
                    lo = mid + 1
                else:
                    hi = mid - 1

            if best_len == 0:
                # Even overhead alone (no content) doesn't fit.
                raise ValueError(
                    "Current wrapper/metadata exceeds --size. "
                    "Increase --size, use --no-suffix, or reduce metadata."
                )

            bodies.append(remaining[:best_len])
            remaining = remaining[best_len:]
            idx += 1

        return bodies

    # ---------- Main flow ----------

    def process_files(self, args):
        """Process files according to the provided arguments."""
        # Decide whether to inline FILE headers inside the content.
        # Keep existing behavior (headers on) unless you later add a flag.

        content = read_files(args.file) if hasattr(read_files, "__call__") else read_files(args.file)
        if not content.strip():
            print("No content found in any of the specified files.")
            return

        # Build chunk bodies under a TOTAL size budget (final output length).
        try:
            bodies = self._emit_bodies_budgeted(content, args.size, args)
        except ValueError as e:
            print(f"Error: {e}")
            return

        total_chunks = len(bodies)

        # Which chunk are we on?
        current_idx = read_state()
        if current_idx >= total_chunks:
            print("All chunks processed! Use --reset to start over.")
            return

        # Prepare this chunk with REAL prompt and REAL total
        raw_body = bodies[current_idx]
        masked_body = mask_secrets(raw_body, self.regex_patterns)

        chunk_info = {
            "chunk": masked_body,
            "index": current_idx,
            "total": total_chunks,
            "is_last": current_idx == total_chunks - 1,
            "is_first": current_idx == 0,
        }

        prompt_text = create_prompt_text(args.prompt, self.config, chunk_info, args)
        json_wrapper = format_json_wrapper(prompt_text, masked_body, chunk_info, args, self.config)

        # Final guard (paranoid): ensure we never exceed the budget we promised.
        if len(json_wrapper) > args.size:
            # Extremely unlikely due to pessimistic measurement, but defend anyway.
            # Trim a few chars and re-wrap.
            overflow = len(json_wrapper) - args.size
            if overflow > 0 and len(masked_body) > overflow:
                masked_body = masked_body[:-overflow]
                chunk_info["chunk"] = masked_body
                json_wrapper = format_json_wrapper(prompt_text, masked_body, chunk_info, args, self.config)

        # Output and update state
        success = output_chunk(json_wrapper, args, chunk_info)
        if success:
            write_state(current_idx + 1)
            print_progress_info(args, chunk_info)

    def get_current_chunk(self):
        """Get information about the current chunk without processing."""
        return read_state()

    def should_continue_processing(self, total_chunks):
        """Check if there are more chunks to process."""
        return read_state() < total_chunks
