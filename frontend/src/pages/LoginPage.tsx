import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import TextField from '@mui/material/TextField';
import Typography from '@mui/material/Typography';
import { useForm } from 'react-hook-form';
import { yupResolver } from '@hookform/resolvers/yup';
import * as yup from 'yup';
import { useAuth } from '../contexts/AuthContext';
import { LoginFormData } from '../types';
import Mark from '../components/Mark';
import { color, font, size, space } from '../theme/tokens';

/**
 * Riot IDs are 3–16 characters and may contain spaces and accented letters, so
 * the old alphanumeric-only rule rejected legitimate accounts. Length and a
 * no-edge-whitespace rule are all that can be checked here; whether the account
 * exists is Riot's answer to give, not ours.
 */
const schema = yup.object({
  riot_id: yup
    .string()
    .required('Enter your Riot ID')
    .min(3, 'Riot IDs are at least 3 characters')
    .max(16, 'Riot IDs are at most 16 characters')
    .matches(/^\S(.*\S)?$/, 'Remove the leading or trailing space'),
  tag: yup
    .string()
    .required('Enter your tag')
    .min(3, 'Tags are 3 to 5 characters')
    .max(5, 'Tags are 3 to 5 characters')
    .matches(/^[a-zA-Z0-9]+$/, 'Tags are letters and numbers only'),
});

const LoginPage: React.FC = () => {
  const navigate = useNavigate();
  const { login } = useAuth();
  const [error, setError] = useState<string>('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<LoginFormData>({ resolver: yupResolver(schema) });

  const onSubmit = async (data: LoginFormData) => {
    setIsSubmitting(true);
    setError('');
    try {
      await login({ riot_id: data.riot_id.trim(), tag: data.tag.trim() });
      navigate('/dashboard');
    } catch (err: any) {
      // Only a 404 means the Riot ID is actually wrong. Everything else is a
      // problem on this end, and saying so stops people retyping a name that
      // was never the issue.
      if (err?.status === 404) {
        setError(
          `Riot has no account for ${data.riot_id.trim()}#${data.tag.trim()}. Check the spelling and the tag.`,
        );
      } else if (err?.status === 429) {
        setError('Riot is rate limiting this server. Try again in a minute.');
      } else {
        setError('Account lookup is unavailable right now. This is a problem here, not with your Riot ID.');
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Box
      sx={{
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        paddingInline: { xs: `${space[4]}px`, md: `${space[8]}px` },
        paddingBlock: `${space[7]}px`,
      }}
    >
      {/* Left-aligned and narrow rather than a centred card: this is one short
          task, and the measure is what keeps it readable, not a container. */}
      <Box sx={{ width: '100%', maxWidth: 420 }}>
        <Mark size={22} />
        <Typography
          component="h1"
          sx={{
            fontFamily: font.display,
            fontWeight: 600,
            fontSize: 30,
            lineHeight: 1.15,
            color: color.textHi,
            marginTop: `${space[3]}px`,
          }}
        >
          League Analytics
        </Typography>
        <Typography variant="body2" sx={{ color: color.text, marginTop: `${space[3]}px`, maxWidth: size.prose }}>
          Every number here comes from matches you have played.
        </Typography>

        <Box
          component="form"
          onSubmit={handleSubmit(onSubmit)}
          noValidate
          sx={{ marginTop: `${space[7]}px` }}
        >
          <Typography component="h2" variant="overline" sx={{ color: color.textLo, display: 'block' }}>
            Riot ID
          </Typography>

          {/* Name and tag sit on one row because they are one identifier, and
              the "#" is printed between them the way Riot writes it. */}
          <Box
            sx={{
              display: 'flex',
              alignItems: 'flex-start',
              gap: `${space[2]}px`,
              marginTop: `${space[2]}px`,
            }}
          >
            <TextField
              {...register('riot_id')}
              id="riot_id"
              label="Name"
              autoComplete="username"
              autoFocus
              fullWidth
              error={!!errors.riot_id}
              helperText={errors.riot_id?.message}
              inputProps={{ 'aria-invalid': !!errors.riot_id }}
            />
            <Typography
              aria-hidden="true"
              sx={{ color: color.textLo, fontSize: 15, lineHeight: `${size.control}px`, flexShrink: 0 }}
            >
              #
            </Typography>
            <TextField
              {...register('tag')}
              id="tag"
              label="Tag"
              autoComplete="off"
              error={!!errors.tag}
              helperText={errors.tag?.message}
              inputProps={{ 'aria-invalid': !!errors.tag }}
              sx={{ width: 96, flexShrink: 0 }}
            />
          </Box>

          {error && (
            <Typography
              role="alert"
              variant="body2"
              sx={{
                color: color.loss,
                marginTop: `${space[4]}px`,
                paddingLeft: `${space[3]}px`,
                borderLeft: `2px solid ${color.loss}`,
              }}
            >
              {error}
            </Typography>
          )}

          <Button
            type="submit"
            variant="contained"
            disabled={isSubmitting}
            sx={{ marginTop: `${space[5]}px` }}
          >
            {isSubmitting ? 'Checking with Riot…' : 'Find my account'}
          </Button>
        </Box>

        <Typography
          variant="caption"
          sx={{
            display: 'block',
            marginTop: `${space[7]}px`,
            paddingTop: `${space[4]}px`,
            borderTop: `1px solid ${color.rule}`,
            maxWidth: size.prose,
          }}
        >
          There is no password and no sign-up. Your Riot ID is checked against Riot&apos;s account
          service; if it has not been seen here before, an entry is created for it.
        </Typography>
      </Box>
    </Box>
  );
};

export default LoginPage;
